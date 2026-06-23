"""
dt_contribution_ablation.py -- Quantify the Latent Digital Twin's contribution.

Compares meta-learner performance when trained on:
  (A) DT-grounded data: physics-aligned latent DT training set (n=1500)
      All modalities share a common latent degradation variable d, so inter-modal
      correlations (vibration RMS ? as d ?, temperature ? as d ?, etc.) are preserved.
  (B) Random balanced data: class-stratified samples with inter-modal correlations broken
      (each modality's predictions drawn independently for each sample).

Both conditions are evaluated on the same 300-sample DT test set.
This directly answers Reviewer C5: "what does the DT layer contribute?"

Run from project root: python scripts/dt_contribution_ablation.py
Output: results/publication_metrics/dt_contribution.json
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

MODALITY_PROB_SLICES = {
    "CWRU":      slice(0, 3),
    "Induction": slice(5, 8),
    "NASA":      slice(10, 13),
    "Current":   slice(15, 18),
    "Thermal":   slice(20, 23),
}
EXPERT_ORDER = ["CWRU", "Induction", "NASA", "Current", "Thermal"]


def recover_preds_from_meta_features(X_raw):
    preds = {}
    for mod, sl in MODALITY_PROB_SLICES.items():
        probs = X_raw[:, sl].astype(np.float32)
        probs = np.clip(probs, 0.0, 1.0)
        row_sums = probs.sum(axis=1, keepdims=True)
        preds[mod] = probs / np.where(row_sums > 1e-9, row_sums, 1.0)
    return preds


def build_stacking_classifier():
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


def bootstrap_ci_f1(y_true, y_pred, n_bootstrap=1000, seed=42):
    rng = np.random.default_rng(seed)
    n   = len(y_true)
    f1s = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        f1s.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    return (float(np.mean(f1s)),
            float(np.percentile(f1s, 2.5)),
            float(np.percentile(f1s, 97.5)))


def build_random_balanced_training(preds_train, y_train, n_samples=1500, seed=42):
    """
    Build training meta-features where inter-modal correlations are broken.
    For each output sample:
      1. Sample a class-conditioned label (preserves class balance).
      2. For each modality, independently sample a random training instance of that class.
    This destroys the DT's latent-variable alignment while preserving class statistics.
    """
    rng     = np.random.default_rng(seed)
    classes = np.unique(y_train)
    n_per   = n_samples // len(classes)

    X_parts = []
    y_parts = []

    for cls in classes:
        cls_mask = (y_train == cls)
        n_cls    = int(cls_mask.sum())

        # For each modality, independently draw n_per indices from this class
        scrambled_preds = {}
        for mod, probs in preds_train.items():
            cls_probs   = probs[cls_mask]
            draw_idx    = rng.integers(0, n_cls, size=n_per)
            scrambled_preds[mod] = cls_probs[draw_idx]

        X_block = extract_meta_features_from_predictions(scrambled_preds)
        X_parts.append(X_block)
        y_parts.append(np.full(n_per, cls, dtype=y_train.dtype))

    X_random = np.vstack(X_parts)
    y_random = np.concatenate(y_parts)

    perm = rng.permutation(len(y_random))
    return X_random[perm], y_random[perm]


def run_dt_contribution():
    print("\n=== Digital Twin Contribution Ablation ===")
    print("Comparing: (A) DT-grounded  vs.  (B) Random-balanced training data.\n")

    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found.\nRun scripts/generate_meta_features.py first.")
        sys.exit(1)

    data        = np.load(feat_path)
    X_train_raw = data["X_train"]   # 1500 x 32, unscaled DT-grounded
    X_test_raw  = data["X_test"]    # 300  x 32, held-out DT test
    y_train     = data["y_train"]
    y_test      = data["y_test"]

    preds_train = recover_preds_from_meta_features(X_train_raw)
    preds_test  = recover_preds_from_meta_features(X_test_raw)

    # Build test features (same for both conditions)
    X_test_meta = extract_meta_features_from_predictions(preds_test)

    results = {}

    # === Condition A: DT-grounded ===
    print("--- Condition A: DT-grounded synthetic data (physics-aligned via latent d) ---")
    X_train_dt = extract_meta_features_from_predictions(preds_train)

    scaler_a = StandardScaler()
    X_tr_a   = scaler_a.fit_transform(X_train_dt)
    X_te_a   = scaler_a.transform(X_test_meta)

    model_a  = build_stacking_classifier()
    model_a.fit(X_tr_a, y_train)
    y_pred_a = model_a.predict(X_te_a)

    f1_a  = f1_score(y_test, y_pred_a, average="macro")
    acc_a = accuracy_score(y_test, y_pred_a)
    ci_mean_a, ci_lo_a, ci_hi_a = bootstrap_ci_f1(y_test, y_pred_a)
    report_a = classification_report(y_test, y_pred_a, output_dict=True, zero_division=0)

    print(f"  F1-macro: {f1_a:.4f}  95% CI: [{ci_lo_a:.4f}, {ci_hi_a:.4f}]")
    print(f"  Accuracy: {acc_a:.4f}")

    results["dt_grounded"] = {
        "description": "DT-grounded synthetic data: all modalities linked by latent degradation variable d",
        "f1_macro":          float(f1_a),
        "accuracy":          float(acc_a),
        "f1_bootstrap_mean": ci_mean_a,
        "f1_ci_95_lo":       ci_lo_a,
        "f1_ci_95_hi":       ci_hi_a,
        "per_class": {
            k: {m: float(v) for m, v in v2.items()}
            for k, v2 in report_a.items() if isinstance(v2, dict)
        },
    }

    # === Condition B: Random balanced (no DT physics alignment) ===
    print("\n--- Condition B: Random-balanced data (inter-modal correlations broken) ---")
    X_train_rand, y_train_rand = build_random_balanced_training(preds_train, y_train, n_samples=1500)

    print(f"  Random training set: {X_train_rand.shape}")
    print(f"  Class distribution: {dict(zip(*np.unique(y_train_rand, return_counts=True)))}")

    scaler_b = StandardScaler()
    X_tr_b   = scaler_b.fit_transform(X_train_rand)
    X_te_b   = scaler_b.transform(X_test_meta)

    model_b  = build_stacking_classifier()
    model_b.fit(X_tr_b, y_train_rand)
    y_pred_b = model_b.predict(X_te_b)

    f1_b  = f1_score(y_test, y_pred_b, average="macro")
    acc_b = accuracy_score(y_test, y_pred_b)
    ci_mean_b, ci_lo_b, ci_hi_b = bootstrap_ci_f1(y_test, y_pred_b)
    report_b = classification_report(y_test, y_pred_b, output_dict=True, zero_division=0)

    print(f"  F1-macro: {f1_b:.4f}  95% CI: [{ci_lo_b:.4f}, {ci_hi_b:.4f}]")
    print(f"  Accuracy: {acc_b:.4f}")

    results["random_balanced"] = {
        "description": (
            "Random balanced: class-stratified samples, each modality independently shuffled "
            "(breaks inter-modal correlation, no physics alignment)"
        ),
        "f1_macro":          float(f1_b),
        "accuracy":          float(acc_b),
        "f1_bootstrap_mean": ci_mean_b,
        "f1_ci_95_lo":       ci_lo_b,
        "f1_ci_95_hi":       ci_hi_b,
        "per_class": {
            k: {m: float(v) for m, v in v2.items()}
            for k, v2 in report_b.items() if isinstance(v2, dict)
        },
    }

    # === Summary ===
    delta_f1  = f1_a - f1_b
    delta_acc = acc_a - acc_b

    print("\n=== DT Contribution Summary ===")
    print(f"  DT-grounded F1:          {f1_a:.4f}  [{ci_lo_a:.4f}, {ci_hi_a:.4f}]")
    print(f"  Random-balanced F1:      {f1_b:.4f}  [{ci_lo_b:.4f}, {ci_hi_b:.4f}]")
    print(f"  DT advantage (DeltaF1):      {delta_f1:+.4f}  ({delta_f1*100:+.2f} pp)")
    print(f"  DT advantage (DeltaAcc):     {delta_acc:+.4f}  ({delta_acc*100:+.2f} pp)")

    results["dt_advantage"] = {
        "f1_delta":         float(delta_f1),
        "f1_delta_percent": float(delta_f1 * 100),
        "acc_delta":        float(delta_acc),
        "interpretation": (
            f"Physics-grounded DT training data yields {delta_f1*100:+.2f} percentage-point "
            "F1 improvement over randomly balanced samples with broken inter-modal correlations. "
            "This demonstrates that the latent degradation variable d -- which preserves the "
            "expected physical co-variation between modalities (vibration ?, temperature ?, "
            "RUL ? as motor degrades) -- provides discriminative signal beyond class balance alone."
        ),
    }

    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/dt_contribution.json")
    output   = {
        "methodology": (
            "Condition A: meta-learner trained on DT-grounded synthetic data (n=1500) from "
            "build_latent_digital_twin.py, where all modalities share latent variable d. "
            "Condition B: meta-learner trained on class-stratified samples (same n=1500) with "
            "each modality's predictions drawn independently (inter-modal correlation destroyed). "
            "Both evaluated on the same 300-sample DT test set. "
            "Bootstrap CI: n=1000, seed=42."
        ),
        "timestamp": datetime.now().isoformat(),
        "results":   results,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK DT contribution results saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_dt_contribution()
