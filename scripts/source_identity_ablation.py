"""
source_identity_ablation.py -- Devil's Advocate: does source identity explain the results?

The strongest counter-argument from Reviewer 5:
  "The XGBoost meta-learner is doing its job; the job just isn't multimodal sensor fusion.
   It learns 'if the feature distribution looks like CWRU -> predict per CWRU projection'.
   The right ablation: replace meta-features with random-permuted entropies/margins.
   If still >85%, entropies/margins are not the signal -- source identity is."

This script tests THREE specific hypotheses:

Test 1 -- SOURCE INDICATOR ONLY
  Build a 5-dim feature: for each sample, which of the 5 experts has the highest
  confidence? Train a simple logistic regression on just this 5-dim one-hot.
  If F1 ~= meta-fusion F1, source identity IS the primary signal.

Test 2 -- PERMUTED ENTROPY/MARGIN ABLATION (reviewer's exact proposal)
  Randomly shuffle entropy and margin values independently across samples
  (within each expert's slot, shuffle only dims 3 and 4 of the 5-dim block).
  Retrain the meta-learner on permuted features.
  If F1 stays high, entropy/margin add no signal beyond the base probabilities.

Test 3 -- SHUFFLED META-FEATURES CONTROL
  Randomly permute the entire meta-feature matrix across samples (shuffles
  label-feature correspondence). Expected result: ~33% accuracy (chance level).
  This is a sanity check -- if it fails, something is wrong.

Test 4 -- BASE PROBABILITIES ONLY (no entropy/margin/global stats)
  Train meta-learner on only the 15 base probability dimensions (3 per expert).
  Compare to the full 32-dim model. The gap shows how much entropy/margin contribute.

Run from project root: python scripts/source_identity_ablation.py
Output: results/publication_metrics/source_identity_ablation.json
"""
import os
import sys
import json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from datetime import datetime

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

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
# Entropy and margin are dims 3 and 4 within each 5-dim block
EXPERT_ENT_IDX   = [3, 8, 13, 18, 23]   # entropy positions in 32-dim vector
EXPERT_MARG_IDX  = [4, 9, 14, 19, 24]   # margin positions in 32-dim vector


def build_stacking_classifier(seed=42):
    if HAS_XGB:
        experts = [
            ("xgb", xgb.XGBClassifier(
                n_estimators=150, max_depth=4, learning_rate=0.05,
                min_child_weight=5, subsample=0.8, random_state=seed,
                eval_metric="mlogloss", verbosity=0)),
            ("rf",  RandomForestClassifier(n_estimators=100, max_depth=8, random_state=seed)),
            ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500,
                                  alpha=0.05, random_state=seed)),
        ]
    else:
        experts = [
            ("rf",  RandomForestClassifier(n_estimators=100, max_depth=8, random_state=seed)),
            ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500,
                                  alpha=0.05, random_state=seed)),
        ]
    judge = MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu",
                          alpha=0.01, max_iter=2000, random_state=seed)
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
    return float(np.mean(f1s)), float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5))


def eval_model(name, X_train, y_train, X_test, y_test, classifier="stacking"):
    scaler  = StandardScaler()
    Xtr     = scaler.fit_transform(X_train)
    Xte     = scaler.transform(X_test)

    if classifier == "logistic":
        model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    else:
        model = build_stacking_classifier()

    model.fit(Xtr, y_train)
    y_pred = model.predict(Xte)

    f1   = float(f1_score(y_test, y_pred, average="macro"))
    acc  = float(accuracy_score(y_test, y_pred))
    f1m, f1lo, f1hi = bootstrap_ci_f1(y_test, y_pred)

    print(f"  {name:<42} F1={f1:.4f}  [{f1lo:.4f},{f1hi:.4f}]  Acc={acc:.4f}")
    return {"name": name, "f1_macro": f1, "accuracy": acc,
            "f1_ci_lo": f1lo, "f1_ci_hi": f1hi}


def run_source_identity_ablation():
    print("\n=== Source Identity Ablation (Devil's Advocate Tests) ===\n")

    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found. Run generate_meta_features.py first.")
        sys.exit(1)

    data        = np.load(feat_path)
    X_train_raw = data["X_train"]   # 1500 x 32
    X_test_raw  = data["X_test"]    # 300  x 32
    y_train     = data["y_train"]
    y_test      = data["y_test"]

    rng = np.random.default_rng(42)

    print(f"{'Test':<42} {'F1':>7}  {'95% CI':>15}  {'Acc':>7}")
    print("-" * 78)

    results = {}

    # ?? Reference: full 32-dim meta-features (should match official_results.json) ?
    ref = eval_model("Full 32-dim meta-features (reference)",
                     X_train_raw, y_train, X_test_raw, y_test)
    results["full_32dim_reference"] = ref

    # ?? Test 1: SOURCE INDICATOR ONLY (5-dim one-hot) ??????????????????????????
    def build_source_indicator(X_raw):
        """5-dim: softmax-confidence of each expert (not one-hot, but which expert dominates)."""
        indicator = np.zeros((len(X_raw), 5), dtype=float)
        for j, sl in enumerate(MODALITY_PROB_SLICES.values()):
            indicator[:, j] = X_raw[:, sl].max(axis=1)   # max confidence per expert
        return indicator

    X_si_train = build_source_indicator(X_train_raw)
    X_si_test  = build_source_indicator(X_test_raw)

    si = eval_model("Source indicator only (which expert dominates)",
                    X_si_train, y_train, X_si_test, y_test, classifier="logistic")
    results["source_indicator_only_logistic"] = si

    si_s = eval_model("Source indicator only (stacking)",
                      X_si_train, y_train, X_si_test, y_test)
    results["source_indicator_only_stacking"] = si_s

    results["source_id_interpretation"] = (
        f"If source-indicator F1 ({si['f1_macro']:.4f}) ~= full model F1 "
        f"({ref['f1_macro']:.4f}), source identity explains the result. "
        f"Gap = {ref['f1_macro'] - si['f1_macro']:+.4f}."
    )

    # ?? Test 2: PERMUTED ENTROPY/MARGIN (reviewer's exact proposal) ?????????????
    def permute_entropy_margin(X_raw, seed=99):
        rng_p  = np.random.default_rng(seed)
        X_perm = X_raw.copy()
        n      = len(X_raw)
        for col_idx in EXPERT_ENT_IDX + EXPERT_MARG_IDX:
            X_perm[:, col_idx] = X_raw[rng_p.permutation(n), col_idx]
        return X_perm

    X_perm_train = permute_entropy_margin(X_train_raw, seed=99)
    X_perm_test  = permute_entropy_margin(X_test_raw,  seed=99)

    pe = eval_model("Permuted entropy+margin (reviewer's ablation)",
                    X_perm_train, y_train, X_perm_test, y_test)
    results["permuted_entropy_margin"] = pe

    results["entropy_margin_interpretation"] = (
        f"If permuted-entropy model F1 ({pe['f1_macro']:.4f}) ~= full model F1 "
        f"({ref['f1_macro']:.4f}), entropy/margin add no signal beyond base probs. "
        f"Gap = {ref['f1_macro'] - pe['f1_macro']:+.4f}."
    )

    # ?? Test 3: SHUFFLED LABELS CONTROL (sanity check: should give ~33%) ???????
    y_shuffled = rng.permutation(y_train)
    ctrl = eval_model("Shuffled labels control (expect ~33% F1)",
                      X_train_raw, y_shuffled, X_test_raw, y_test)
    results["shuffled_labels_control"] = ctrl

    # ?? Test 4: BASE PROBABILITIES ONLY (15 dims, no entropy/margin/global) ????
    # Extract only the 15 probability dims from the 32-dim vector
    prob_cols = list(range(0, 3)) + list(range(5, 8)) + list(range(10, 13)) + \
                list(range(15, 18)) + list(range(20, 23))

    X_probs_train = X_train_raw[:, prob_cols]
    X_probs_test  = X_test_raw[:, prob_cols]

    bp = eval_model("Base probabilities only (15-dim, no entropy/margin)",
                    X_probs_train, y_train, X_probs_test, y_test)
    results["base_probs_only_15dim"] = bp

    results["entropy_margin_contribution"] = (
        f"Adding entropy/margin/global stats (15->32 dims) changes F1 by "
        f"{ref['f1_macro'] - bp['f1_macro']:+.4f}."
    )

    # ?? Summary ??????????????????????????????????????????????????????????????????
    print("\n=== Interpretation ===")
    gap_si  = ref["f1_macro"] - si["f1_macro"]
    gap_pe  = ref["f1_macro"] - pe["f1_macro"]
    gap_bp  = ref["f1_macro"] - bp["f1_macro"]

    verdict_si = (
        "CONFIRMED: source ID explains most of the result -- significant further work needed."
        if gap_si < 0.05 else
        "REFUTED: source ID alone is insufficient; meta-features carry additional signal."
    )
    verdict_pe = (
        "CONFIRMED: entropy/margin add no signal beyond base probs."
        if gap_pe < 0.03 else
        "REFUTED: entropy/margin carry meaningful signal."
    )

    print(f"  Source ID hypothesis:      {verdict_si}  (gap={gap_si:+.4f})")
    print(f"  Entropy/margin hypothesis: {verdict_pe}  (gap={gap_pe:+.4f})")
    print(f"  Entropy/margin contribution to F1: {gap_bp:+.4f} (vs base-probs-only)")

    results["verdicts"] = {
        "source_id_hypothesis":      verdict_si,
        "entropy_margin_hypothesis": verdict_pe,
        "f1_gaps": {
            "full_vs_source_indicator": round(gap_si, 4),
            "full_vs_permuted_ent_marg": round(gap_pe, 4),
            "full_vs_base_probs_only":  round(gap_bp, 4),
        },
    }

    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/source_identity_ablation.json")
    output   = {
        "methodology": (
            "Tests whether the meta-learner exploits source identity rather than sensor fusion. "
            "Test 1: trains on 5-dim 'which expert dominates' feature only. "
            "Test 2: permutes entropy and margin values across samples, retrains. "
            "Test 3: shuffles labels (sanity check, expect ~33%). "
            "Test 4: uses only 15 base probability dims, no entropy/margin/global stats. "
            "Bootstrap CI: n=1000, seed=42."
        ),
        "timestamp": datetime.now().isoformat(),
        "results":   results,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Source identity ablation saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_source_identity_ablation()
