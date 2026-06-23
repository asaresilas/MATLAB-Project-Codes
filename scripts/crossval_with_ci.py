"""
crossval_with_ci.py -- 5-fold stratified CV, bootstrap CIs, and McNemar's test.

Uses the full 1800-sample latent DT dataset (1500 train + 300 test combined).
Reports mean +/- 95% CI for F1, Accuracy, and AUC for the meta-fusion model.

McNemar's test (with continuity correction) vs. three baselines:
  - Majority Class:    always predict the most frequent class
  - Late Fusion:       argmax of mean probability across 5 experts (no training)
  - CWRU Single Model: argmax of CWRU expert probabilities only

Run from project root: python scripts/crossval_with_ci.py
Output: results/publication_metrics/crossval_ci.json
"""
import os
import sys
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, accuracy_score, roc_auc_score
from sklearn.preprocessing import label_binarize, StandardScaler
from scipy.stats import chi2 as chi2_dist
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

MODALITY_PROB_SLICES = {
    "CWRU":      slice(0, 3),
    "Induction": slice(5, 8),
    "NASA":      slice(10, 13),
    "Current":   slice(15, 18),
    "Thermal":   slice(20, 23),
}


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
    return StackingClassifier(estimators=experts, final_estimator=judge, cv=10, n_jobs=1)


def mcnemar_test(y_true, y_pred_a, y_pred_b):
    """McNemar's test with continuity correction: A vs B."""
    correct_a = (y_pred_a == y_true)
    correct_b = (y_pred_b == y_true)
    b = int(np.sum( correct_a & ~correct_b))  # A right, B wrong
    c = int(np.sum(~correct_a &  correct_b))  # A wrong, B right
    if b + c == 0:
        return 1.0, 0.0
    chi2_val = (abs(b - c) - 1.0) ** 2 / (b + c)
    p_value  = float(1.0 - chi2_dist.cdf(chi2_val, df=1))
    return p_value, float(chi2_val)


def bootstrap_ci_f1(y_true, y_pred, n_bootstrap=1000, ci=95, seed=42):
    rng  = np.random.default_rng(seed)
    n    = len(y_true)
    f1s  = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        f1s.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    lo = np.percentile(f1s, (100 - ci) / 2)
    hi = np.percentile(f1s, 100 - (100 - ci) / 2)
    return float(np.mean(f1s)), float(lo), float(hi)


def ci_from_folds(vals, ci=95):
    arr = np.asarray(vals, dtype=float)
    mean = float(arr.mean())
    se   = float(arr.std() / np.sqrt(len(arr)))
    z    = 1.96   # 95% CI
    return {"mean": mean, "std": float(arr.std()),
            "ci_95_lo": mean - z * se, "ci_95_hi": mean + z * se,
            "folds": [float(v) for v in arr]}


def run_crossval():
    print("\n=== 5-Fold Stratified Cross-Validation with Confidence Intervals ===\n")

    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found.\nRun scripts/generate_meta_features.py first.")
        sys.exit(1)

    data  = np.load(feat_path)
    X_all = np.vstack([data["X_train"], data["X_test"]])
    y_all = np.concatenate([data["y_train"], data["y_test"]])

    print(f"Full dataset: {X_all.shape[0]} samples, {X_all.shape[1]} features")
    print(f"Class distribution: {dict(zip(*np.unique(y_all, return_counts=True)))}")

    # Build baseline predictions from meta-feature arrays (no model training)
    late_preds = np.zeros(len(y_all), dtype=int)
    cwru_preds = np.zeros(len(y_all), dtype=int)
    for i in range(len(y_all)):
        mean_p = np.zeros(3, dtype=float)
        for sl in MODALITY_PROB_SLICES.values():
            mean_p += X_all[i, sl]
        late_preds[i] = int(np.argmax(mean_p))
        cwru_preds[i] = int(np.argmax(X_all[i, MODALITY_PROB_SLICES["CWRU"]]))

    majority_class = int(np.bincount(y_all).argmax())
    majority_preds = np.full(len(y_all), majority_class, dtype=int)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    fold_metrics = {
        "meta_fusion": {"f1": [], "acc": [], "auc": []},
        "late_fusion": {"f1": [], "acc": []},
        "cwru_only":   {"f1": [], "acc": []},
        "majority":    {"f1": [], "acc": []},
    }

    oof_preds = np.zeros(len(y_all), dtype=int)
    oof_probs = np.zeros((len(y_all), 3), dtype=float)

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X_all, y_all)):
        print(f"  Fold {fold_idx + 1}/5 ...", end=" ", flush=True)

        X_tr, X_te = X_all[train_idx], X_all[test_idx]
        y_tr, y_te = y_all[train_idx],  y_all[test_idx]

        scaler  = StandardScaler()
        X_tr_s  = scaler.fit_transform(X_tr)
        X_te_s  = scaler.transform(X_te)

        model   = build_stacking_classifier()
        model.fit(X_tr_s, y_tr)

        y_pred  = model.predict(X_te_s)
        y_prob  = model.predict_proba(X_te_s)

        oof_preds[test_idx] = y_pred
        oof_probs[test_idx] = y_prob

        y_te_bin = label_binarize(y_te, classes=[0, 1, 2])

        f1  = f1_score(y_te, y_pred, average="macro")
        acc = accuracy_score(y_te, y_pred)
        auc = roc_auc_score(y_te_bin, y_prob, multi_class="ovr", average="macro")

        fold_metrics["meta_fusion"]["f1"].append(f1)
        fold_metrics["meta_fusion"]["acc"].append(acc)
        fold_metrics["meta_fusion"]["auc"].append(auc)

        fold_metrics["late_fusion"]["f1"].append(
            f1_score(y_te, late_preds[test_idx], average="macro"))
        fold_metrics["late_fusion"]["acc"].append(
            accuracy_score(y_te, late_preds[test_idx]))

        fold_metrics["cwru_only"]["f1"].append(
            f1_score(y_te, cwru_preds[test_idx], average="macro"))
        fold_metrics["cwru_only"]["acc"].append(
            accuracy_score(y_te, cwru_preds[test_idx]))

        fold_metrics["majority"]["f1"].append(
            f1_score(y_te, majority_preds[test_idx], average="macro", zero_division=0))
        fold_metrics["majority"]["acc"].append(
            accuracy_score(y_te, majority_preds[test_idx]))

        print(f"F1={f1:.4f}")

    cv_summary = {
        name: {metric: ci_from_folds(vals) for metric, vals in metrics.items()}
        for name, metrics in fold_metrics.items()
    }

    f1_boot_mean, f1_boot_lo, f1_boot_hi = bootstrap_ci_f1(y_all, oof_preds)

    baselines = {
        "majority_class":     majority_preds,
        "late_fusion":        late_preds,
        "cwru_single_model":  cwru_preds,
    }
    mcnemar_results = {}
    for bl_name, bl_pred in baselines.items():
        p, chi2_val = mcnemar_test(y_all, oof_preds, bl_pred)
        mcnemar_results[bl_name] = {
            "p_value":    p,
            "chi2":       chi2_val,
            "significant": bool(p < 0.05),
            "interpretation": (
                f"Meta-Fusion significantly better than {bl_name}: "
                f"{'YES (p={:.4f})'.format(p) if p < 0.05 else 'NO (p={:.4f})'.format(p)}"
            ),
        }

    # Print summary
    mf = cv_summary["meta_fusion"]
    print("\n=== 5-Fold CV Summary ===")
    print(f"  F1-macro:  {mf['f1']['mean']:.4f} +/- {mf['f1']['std']:.4f}  "
          f"95% CI: [{mf['f1']['ci_95_lo']:.4f}, {mf['f1']['ci_95_hi']:.4f}]")
    print(f"  Accuracy:  {mf['acc']['mean']:.4f} +/- {mf['acc']['std']:.4f}")
    print(f"  AUC-macro: {mf['auc']['mean']:.4f} +/- {mf['auc']['std']:.4f}")
    print(f"\n  Bootstrap F1 (pooled OOF, n=1000): {f1_boot_mean:.4f}  "
          f"95% CI: [{f1_boot_lo:.4f}, {f1_boot_hi:.4f}]")

    print("\n  McNemar's Test (continuity-corrected):")
    for bl_name, res in mcnemar_results.items():
        sig = "SIGNIFICANT" if res["significant"] else "NOT significant"
        print(f"    vs {bl_name:<22}: p={res['p_value']:.4f}, chi^2={res['chi2']:.2f}  [{sig}]")

    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/crossval_ci.json")
    output = {
        "methodology": (
            "5-fold stratified CV on full 1800-sample latent DT dataset (1500+300). "
            "Bootstrap CI: n=1000 resamples, seed=42. "
            "McNemar's test with continuity correction (chi2, df=1). "
            "Baseline preds computed from saved meta-features without model retraining."
        ),
        "timestamp":        datetime.now().isoformat(),
        "cv_fold_summary":  cv_summary,
        "bootstrap_ci_f1":  {
            "mean": f1_boot_mean, "ci_95_lo": f1_boot_lo, "ci_95_hi": f1_boot_hi,
            "n_bootstrap": 1000,
        },
        "mcnemar_tests":    mcnemar_results,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Cross-validation results saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_crossval()
