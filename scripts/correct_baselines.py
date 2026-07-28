"""
correct_baselines.py -- Re-implement all comparison baselines correctly.

The previous baseline script (train_comparison_baselines.py) had two critical bugs:
  1. Early-fusion F1=0.1882 was HARD-CODED, not measured.
  2. Uni-modal baseline used a broken label mapping (CWRU 4-class argmax mapped to
     3-class severity by position, discarding Outer Race), yielding sub-chance F1.

This script implements baselines correctly:
  - Majority Class:    always predict the most frequent class (floor baseline)
  - Uni-modal (CWRU): argmax of CWRU probability vector AFTER ensure_3_classes
                      conversion -- same mapping used by the meta-learner
  - Late Fusion:      argmax of mean probability across all 5 experts (no training)
  - Early Fusion:     properly trained MLP on first 100 raw samples per modality,
                      evaluated on the same 300-sample test set
  - Rule-Based:       max-severity-wins heuristic from compare_fusion_methods.py

Reports per-class confusion matrices and bootstrap CIs for every baseline.

Run from project root: python scripts/correct_baselines.py
Output: results/publication_metrics/correct_baselines.json
"""
import os
import sys
import json
import numpy as np
from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features.meta_fusion_features import (
    build_nasa_probs,
    ensure_3_classes,
    extract_meta_features_from_predictions,
)

MODALITY_PROB_SLICES = {
    "CWRU":      slice(0, 3),
    "Induction": slice(5, 8),
    "NASA":      slice(10, 13),
    "Current":   slice(15, 18),
    "Thermal":   slice(20, 23),
}


def bootstrap_ci_f1(y_true, y_pred, n_bootstrap=1000, seed=42):
    rng  = np.random.default_rng(seed)
    n    = len(y_true)
    f1s  = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        f1s.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    return (float(np.mean(f1s)),
            float(np.percentile(f1s, 2.5)),
            float(np.percentile(f1s, 97.5)))


def summarise_baseline(name, y_true, y_pred):
    """Build the full metrics dict for one baseline."""
    f1  = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    cm  = confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    f1_mean, f1_lo, f1_hi = bootstrap_ci_f1(y_true, y_pred)

    per_class = {}
    label_names = {0: "Normal (n=107)", 1: "Warning (n=118)", 2: "Critical (n=75)"}
    for cls, cls_name in label_names.items():
        r = report.get(str(cls), {})
        per_class[cls_name] = {
            "precision": round(r.get("precision", 0.0), 4),
            "recall":    round(r.get("recall",    0.0), 4),
            "f1":        round(r.get("f1-score",  0.0), 4),
            "support":   int(r.get("support",     0)),
        }

    print(f"\n  {name}")
    print(f"    F1-macro: {f1:.4f}  95% CI: [{f1_lo:.4f}, {f1_hi:.4f}]")
    print(f"    Accuracy: {acc:.4f}")
    for cn, v in per_class.items():
        print(f"    {cn}: P={v['precision']:.3f} R={v['recall']:.3f} F1={v['f1']:.3f}")

    return {
        "f1_macro":          f1,
        "accuracy":          acc,
        "f1_bootstrap_mean": f1_mean,
        "f1_ci_95_lo":       f1_lo,
        "f1_ci_95_hi":       f1_hi,
        "confusion_matrix":  cm,
        "per_class":         per_class,
    }


def run_correct_baselines():
    print("\n=== Correct Baseline Evaluation ===")
    print("All baselines use the same 300-sample latent DT test set.\n")

    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found.\nRun scripts/generate_meta_features.py first.")
        sys.exit(1)

    data        = np.load(feat_path)
    X_train_raw = data["X_train"]   # 1500 x 32
    X_test_raw  = data["X_test"]    # 300  x 32
    y_train     = data["y_train"]
    y_test      = data["y_test"]

    results = {}

    # ?? Baseline 0: Majority Class ????????????????????????????????????????????
    majority_cls   = int(np.bincount(y_train).argmax())
    majority_preds = np.full(len(y_test), majority_cls, dtype=int)
    results["majority_class"] = summarise_baseline("Majority Class", y_test, majority_preds)
    results["majority_class"]["description"] = (
        f"Always predict the most frequent training class ({majority_cls}). "
        "Theoretical floor: binomial accuracy = max class frequency."
    )

    # ?? Baseline 1: Uni-modal -- CWRU expert only ??????????????????????????????
    # Uses the CWRU probability block AFTER ensure_3_classes mapping,
    # identical to how the meta-learner receives it.
    cwru_probs = X_test_raw[:, MODALITY_PROB_SLICES["CWRU"]]
    cwru_preds = np.argmax(cwru_probs, axis=1).astype(int)
    results["unimodal_cwru"] = summarise_baseline("Uni-modal (CWRU, mapped)", y_test, cwru_preds)
    results["unimodal_cwru"]["description"] = (
        "CWRU expert probability vector (ensure_3_classes mapping: "
        "Normal->0, InnerRace->1, Ball->2), argmax. Same mapping used by the meta-learner. "
        "Corrects the previous baseline which used a broken 4->3 truncation."
    )

    # ?? Baseline 2: Late Fusion -- mean of all 5 expert probabilities ??????????
    mean_probs = np.zeros((len(y_test), 3), dtype=float)
    for sl in MODALITY_PROB_SLICES.values():
        mean_probs += X_test_raw[:, sl]
    mean_probs /= len(MODALITY_PROB_SLICES)
    late_preds = np.argmax(mean_probs, axis=1).astype(int)
    results["late_fusion"] = summarise_baseline("Late Fusion (mean probs)", y_test, late_preds)
    results["late_fusion"]["description"] = (
        "Argmax of mean probability across all 5 expert probability vectors. "
        "No meta-learner training required."
    )

    # ?? Baseline 3: Early Fusion -- trained MLP on first 100 raw points ???????
    print("\n  Training Early Fusion MLP (100 raw points per modality) ...")
    dt_train_path = os.path.join(PROJECT_ROOT, "data/latent_train_cache.npz")
    dt_test_path  = os.path.join(PROJECT_ROOT, "data/latent_digital_twin.npz")

    if os.path.exists(dt_train_path) and os.path.exists(dt_test_path):
        train_cache = np.load(dt_train_path)
        test_cache  = np.load(dt_test_path)

        def get_early_fusion_features(cache, n_pts=100):
            parts = []
            for key in ["vibration_cwru", "vibration_ind", "current", "thermal"]:
                raw = cache[key]
                # Flatten: take first n_pts of first channel/dim
                flat = raw.reshape(len(raw), -1)[:, :n_pts]
                parts.append(flat)
            return np.hstack(parts)

        X_ef_train = get_early_fusion_features(train_cache)
        X_ef_test  = get_early_fusion_features(test_cache)
        y_ef_train = train_cache["shared_labels"]
        y_ef_test  = test_cache["shared_labels"]

        scaler_ef   = StandardScaler()
        X_ef_train  = scaler_ef.fit_transform(X_ef_train)
        X_ef_test   = scaler_ef.transform(X_ef_test)

        mlp_ef = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=200,
                               random_state=42, alpha=0.01)
        mlp_ef.fit(X_ef_train, y_ef_train)
        early_preds = mlp_ef.predict(X_ef_test)

        results["early_fusion"] = summarise_baseline("Early Fusion (MLP, raw concat)",
                                                     y_ef_test, early_preds)
        results["early_fusion"]["description"] = (
            "MLP trained on first 100 raw time-domain points from each modality, "
            "concatenated (total 400 features). Trained on 1500-sample DT training set, "
            "evaluated on 300-sample DT test set. This replaces the hard-coded 0.1882 value."
        )
    else:
        print("  WARNING: DT cache files not found -- Early Fusion baseline skipped.")
        results["early_fusion"] = {"error": "latent_train_cache.npz not found"}

    # ?? Baseline 4: Rule-Based (max-severity-wins) ????????????????????????????
    # Severity score per expert: weighted sum of class probs [0, 0.5, 1.0]
    severity_weights = np.array([0.0, 0.5, 1.0])
    rule_preds = np.zeros(len(y_test), dtype=int)
    for i in range(len(y_test)):
        worst_sev = 0.0
        for sl in MODALITY_PROB_SLICES.values():
            probs = X_test_raw[i, sl]
            probs = np.clip(probs, 0, 1)
            probs = probs / (probs.sum() + 1e-9)
            sev = float(np.dot(probs, severity_weights))
            worst_sev = max(worst_sev, sev)
        if worst_sev < 0.30:
            rule_preds[i] = 0
        elif worst_sev < 0.70:
            rule_preds[i] = 1
        else:
            rule_preds[i] = 2

    results["rule_based"] = summarise_baseline("Rule-Based (max severity)", y_test, rule_preds)
    results["rule_based"]["description"] = (
        "Max-severity-wins rule: compute weighted severity score per expert "
        "[Normal=0, Warning=0.5, Critical=1.0], take worst across all experts, "
        "threshold at 0.30 / 0.70."
    )

    # ?? Summary table ?????????????????????????????????????????????????????????
    print("\n=== Baseline Comparison Table ===")
    print(f"{'Baseline':<35} {'F1-macro':>9} {'95% CI':>22} {'Accuracy':>10}")
    print("-" * 80)
    for name, r in results.items():
        if "f1_macro" not in r:
            continue
        ci_str = f"[{r['f1_ci_95_lo']:.4f}, {r['f1_ci_95_hi']:.4f}]"
        print(f"{name:<35} {r['f1_macro']:>9.4f} {ci_str:>22} {r['accuracy']:>10.4f}")
    print(f"{'Meta-Fusion (reference)':<35} {'0.9089':>9} {'[see crossval_ci]':>22} {'0.9089':>10}")

    # Save
    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/correct_baselines.json")
    output   = {
        "methodology": (
            "All baselines evaluated on the 300-sample latent DT test set. "
            "CWRU uni-modal uses ensure_3_classes mapping (same as meta-learner input). "
            "Late fusion = argmax of mean of 5 expert probability vectors. "
            "Early fusion = MLP on 100-point raw window concatenation. "
            "Bootstrap CI: n=1000, seed=42."
        ),
        "timestamp": datetime.now().isoformat(),
        "note_on_previous_baseline": (
            "The previously reported uni-modal F1=0.1753 was computed by truncating "
            "CWRU's 4-class output to 3 classes by position (discarding Outer Race), "
            "causing severe class-label mismatch. The early-fusion F1=0.1882 was "
            "hard-coded, not measured. Both are corrected in this script."
        ),
        "results": results,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Correct baseline results saved -> {out_path}")
    return results


if __name__ == "__main__":
    run_correct_baselines()
