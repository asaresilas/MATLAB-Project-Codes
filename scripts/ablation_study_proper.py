"""
ablation_study_proper.py -- Methodologically correct modality ablation study.

For each ablation scenario the meta-learner is RETRAINED from scratch with the removed
modality's probability vector replaced by a uniform prior [1/3, 1/3, 1/3]. This is
correct versus the previous approach (run_ablation_study.py) which zeroed features in
a pre-trained model at inference time (out-of-distribution evaluation).

Scenarios:
  Full model (all 5 modalities) -- baseline
  Remove Thermal
  Remove Current Signature
  Remove NASA RUL
  Remove Induction Motor
  Remove CWRU (vibration only)

Run from project root: python scripts/ablation_study_proper.py
Output: results/publication_metrics/ablation_proper.json
"""
import os
import sys
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from datetime import datetime

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("WARNING: XGBoost not found -- falling back to RF+MLP ensemble.")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features.meta_fusion_features import extract_meta_features_from_predictions

# Feature layout in the 32-dim meta-feature vector.
# get_rich_features per expert = [p0, p1, p2, entropy, margin] = 5 dims
# Order: CWRU(0-4), Induction(5-9), NASA(10-14), Current(15-19), Thermal(20-24)
# Then: mean_p(25-27), var_p(28-30), global_ent(31)
MODALITY_PROB_SLICES = {
    "CWRU":      slice(0, 3),
    "Induction": slice(5, 8),
    "NASA":      slice(10, 13),
    "Current":   slice(15, 18),
    "Thermal":   slice(20, 23),
}
EXPERT_ORDER = ["CWRU", "Induction", "NASA", "Current", "Thermal"]
UNIFORM_PRIOR = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], dtype=np.float32)


def recover_preds_from_meta_features(X_raw):
    """Recover individual modality probability arrays from the raw meta-feature matrix."""
    preds = {}
    for mod, sl in MODALITY_PROB_SLICES.items():
        probs = X_raw[:, sl].astype(np.float32)
        probs = np.clip(probs, 0.0, 1.0)
        row_sums = probs.sum(axis=1, keepdims=True)
        preds[mod] = probs / np.where(row_sums > 1e-9, row_sums, 1.0)
    return preds


def build_meta_features_with_removal(preds_original, removed_modality):
    """Replace the removed modality with a uniform prior, then recompute meta-features."""
    preds = {mod: p.copy() for mod, p in preds_original.items()}
    if removed_modality is not None:
        n = preds[removed_modality].shape[0]
        preds[removed_modality] = np.tile(UNIFORM_PRIOR, (n, 1))
    return extract_meta_features_from_predictions(preds)


def build_stacking_classifier():
    """Return a fresh StackingClassifier matching production hyperparameters."""
    if HAS_XGB:
        experts = [
            ("xgb", xgb.XGBClassifier(
                n_estimators=150, max_depth=4, learning_rate=0.05,
                min_child_weight=5, subsample=0.8, random_state=42,
                eval_metric="mlogloss", verbosity=0)),
            ("rf",  RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)),
            ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500,
                                  alpha=0.05, random_state=42)),
        ]
    else:
        experts = [
            ("rf",  RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)),
            ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500,
                                  alpha=0.05, random_state=42)),
        ]
    judge = MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu",
                          alpha=0.01, max_iter=2000, random_state=42)
    return StackingClassifier(estimators=experts, final_estimator=judge, cv=10, n_jobs=-1)


def bootstrap_ci_f1(y_true, y_pred, n_bootstrap=1000, ci=95, seed=42):
    rng = np.random.default_rng(seed)
    n   = len(y_true)
    f1s = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        f1s.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    lo = np.percentile(f1s, (100 - ci) / 2)
    hi = np.percentile(f1s, 100 - (100 - ci) / 2)
    return float(np.mean(f1s)), float(lo), float(hi)


def run_ablation():
    print("\n=== Proper Meta-Fusion Ablation Study ===")
    print("Methodology: meta-learner RETRAINED for each modality-removal scenario.\n")

    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found.\nRun scripts/generate_meta_features.py first.")
        sys.exit(1)

    data        = np.load(feat_path)
    X_train_raw = data["X_train"]   # 1500 x 32, unscaled
    X_test_raw  = data["X_test"]    # 300  x 32, unscaled
    y_train     = data["y_train"]
    y_test      = data["y_test"]

    print(f"Loaded: train={X_train_raw.shape}, test={X_test_raw.shape}")
    print(f"Train classes: {dict(zip(*np.unique(y_train, return_counts=True)))}")
    print(f"Test  classes: {dict(zip(*np.unique(y_test,  return_counts=True)))}")

    preds_train = recover_preds_from_meta_features(X_train_raw)
    preds_test  = recover_preds_from_meta_features(X_test_raw)

    scenarios = [
        ("Full Model (baseline)",        None),
        ("Remove Thermal",               "Thermal"),
        ("Remove Current Signature",     "Current"),
        ("Remove NASA RUL",              "NASA"),
        ("Remove Induction Motor",       "Induction"),
        ("Remove CWRU (vibration only)", "CWRU"),
    ]

    results = {}

    for scenario_name, removed in scenarios:
        print(f"\n--- {scenario_name} ---")

        X_tr = build_meta_features_with_removal(preds_train, removed)
        X_te = build_meta_features_with_removal(preds_test,  removed)

        scaler   = StandardScaler()
        X_tr_s   = scaler.fit_transform(X_tr)
        X_te_s   = scaler.transform(X_te)

        model    = build_stacking_classifier()
        model.fit(X_tr_s, y_train)

        y_pred   = model.predict(X_te_s)
        acc      = accuracy_score(y_test, y_pred)
        f1       = f1_score(y_test, y_pred, average="macro")
        f1_mean, f1_lo, f1_hi = bootstrap_ci_f1(y_test, y_pred)
        report   = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        print(f"  Accuracy : {acc:.4f}")
        print(f"  F1-macro : {f1:.4f}  95% CI: [{f1_lo:.4f}, {f1_hi:.4f}]")

        results[scenario_name] = {
            "removed_modality":    removed,
            "accuracy":            float(acc),
            "f1_macro":            float(f1),
            "f1_bootstrap_mean":   f1_mean,
            "f1_ci_95_lo":         f1_lo,
            "f1_ci_95_hi":         f1_hi,
            "delta_vs_full":       None,
            "per_class": {
                k: {m: float(v) for m, v in v2.items()}
                for k, v2 in report.items()
                if isinstance(v2, dict)
            },
        }

    # Compute delta vs. full model
    full_f1 = results["Full Model (baseline)"]["f1_macro"]
    for r in results.values():
        r["delta_vs_full"] = float(r["f1_macro"] - full_f1)

    # Summary table
    print("\n=== Ablation Summary Table ===")
    header = f"{'Scenario':<35} {'F1':>7} {'95% CI':>22} {'D vs Full':>10}"
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        ci_str    = f"[{r['f1_ci_95_lo']:.4f}, {r['f1_ci_95_hi']:.4f}]"
        delta_str = "baseline" if r["delta_vs_full"] == 0.0 else f"{r['delta_vs_full']:+.4f}"
        print(f"{name:<35} {r['f1_macro']:>7.4f} {ci_str:>22} {delta_str:>10}")

    out_dir  = os.path.join(PROJECT_ROOT, "results/publication_metrics")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ablation_proper.json")
    output   = {
        "methodology": (
            "Meta-learner retrained from scratch for each scenario. "
            "Removed modality's probability vector replaced by uniform prior [1/3, 1/3, 1/3] "
            "before recomputing the full 32-dim meta-feature vector. "
            "Bootstrap CI: n=1000, seed=42."
        ),
        "timestamp": datetime.now().isoformat(),
        "results":   results,
    }
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Ablation results saved -> {out_path}")
    return results


if __name__ == "__main__":
    run_ablation()
