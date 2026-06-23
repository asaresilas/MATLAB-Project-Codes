"""
compare_fusion_methods.py -- A/B comparison: Rule-Based vs Meta Fusion.

Data contract
-------------
meta_fusion_features.npz stores UNSCALED features (raw expert probabilities,
entropies, margins, global stats) in X_train/X_test.
meta_fusion_scaler.pkl is the StandardScaler fit on X_train.

The 32-dim feature vector layout (per ablation_study_proper.py):
  [0:3]   CWRU probs        [3]  CWRU entropy  [4]  CWRU margin
  [5:8]   Induction probs   [8]  Ind entropy   [9]  Ind margin
  [10:13] NASA probs        [13] NASA entropy  [14] NASA margin
  [15:18] Current probs     [18] Curr entropy  [19] Curr margin
  [20:23] Thermal probs     [23] Therm entropy [24] Therm margin
  [25:28] global mean_p     [28:31] global var_p   [31] global entropy

Rule-based uses X_test_raw (probabilities are valid [0,1] in the unscaled file).
Meta fusion uses scaler.transform(X_test_raw).

Run from project root: python scripts/compare_fusion_methods.py
Output: results/meta_fusion/fusion_comparison.json
"""

import json
import os
import sys

import joblib
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
)

matplotlib.use("Agg")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

FEATURES_PATH = os.path.join(PROJECT_ROOT, "data", "meta_fusion_features.npz")
SCALER_PATH   = os.path.join(PROJECT_ROOT, "data", "meta_fusion_scaler.pkl")
MODEL_PATH    = os.path.join(PROJECT_ROOT, "Trained_models", "meta_fusion", "meta_fusion_xgb.pkl")

# Per-expert probability slice starts in the 32-dim unscaled vector.
# Each expert block is [p0, p1, p2, entropy, margin] = 5 dims.
EXPERT_PROB_STARTS = {
    "CWRU":      0,
    "Induction": 5,
    "NASA":      10,
    "Current":   15,
    "Thermal":   20,
}


def load_inputs():
    for path, desc in [
        (FEATURES_PATH, "meta_fusion_features.npz (run generate_meta_features.py first)"),
        (SCALER_PATH,   "meta_fusion_scaler.pkl   (run train_meta_fusion.py first)"),
        (MODEL_PATH,    "meta_fusion_xgb.pkl      (run train_meta_fusion.py first)"),
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required file not found:\n  {path}\n  -> {desc}")

    cache = np.load(FEATURES_PATH)
    # X_test in the .npz is UNSCALED -- probabilities in expert slots are valid [0,1]
    X_test_raw = cache["X_test"]
    y_test     = cache["y_test"].astype(int)

    scaler     = joblib.load(SCALER_PATH)
    X_test_scaled = scaler.transform(X_test_raw)  # used only by meta model

    meta_model = joblib.load(MODEL_PATH)
    return X_test_raw, X_test_scaled, y_test, meta_model


def modality_severity_from_probs(raw_row):
    """
    Weighted severity score for each expert from its [0,1]-valued probability triple.
    Returns one score per expert in [0, 1].
    Severity = dot([0.0, 0.5, 1.0], normalised_probs)
    """
    class_weights = np.array([0.0, 0.5, 1.0], dtype=np.float64)
    severities = []
    for start in EXPERT_PROB_STARTS.values():
        probs = np.clip(raw_row[start:start + 3].astype(np.float64), 0.0, 1.0)
        total = probs.sum()
        if total <= 0.0:
            probs = np.ones(3) / 3.0
        else:
            probs = probs / total
        severities.append(float(np.dot(probs, class_weights)))
    return np.array(severities, dtype=np.float64)


def rule_based_predict(raw_row):
    """
    Conservative worst-case rule: classify by the most severely degraded expert.
      score < 0.30 -> Healthy (0)
      score < 0.70 -> Warning (1)
      score >= 0.70 -> Critical (2)
    """
    scores = modality_severity_from_probs(raw_row)
    worst  = float(np.max(scores))
    label  = 0 if worst < 0.30 else (1 if worst < 0.70 else 2)
    return label, worst


def meta_fusion_predict(meta_model, scaled_row):
    probs = meta_model.predict_proba(scaled_row.reshape(1, -1))[0]
    return int(np.argmax(probs)), float(np.max(probs))


def compute_metrics(y_true, y_pred, conf, name):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    fp  = cm[0, 1:].sum()
    tn  = cm[0, 0]
    far = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    return {
        "name":             name,
        "accuracy":         float(accuracy_score(y_true, y_pred)),
        "precision":        float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall":           float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1":               float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "false_alarm_rate": far,
        "avg_confidence":   float(np.mean(conf)),
    }


def main():
    print("\n=== A/B COMPARISON: Rule-Based vs Meta Fusion ===\n")
    X_test_raw, X_test_scaled, y_true, meta_model = load_inputs()
    print(f"  [OK] Test samples       : {len(y_true)}")
    print(f"  [OK] Feature dimensions : {X_test_raw.shape[1]} (unscaled for rule-based)")
    print(f"  [OK] Scaled dims        : {X_test_scaled.shape[1]} (StandardScaler for meta model)")

    y_rule, y_meta     = [], []
    conf_rule, conf_meta = [], []

    for raw_row, scaled_row in zip(X_test_raw, X_test_scaled):
        r_pred, r_conf = rule_based_predict(raw_row)
        m_pred, m_conf = meta_fusion_predict(meta_model, scaled_row)
        y_rule.append(r_pred);  conf_rule.append(r_conf)
        y_meta.append(m_pred);  conf_meta.append(m_conf)

    y_rule  = np.array(y_rule);  y_meta  = np.array(y_meta)
    conf_rule = np.array(conf_rule); conf_meta = np.array(conf_meta)

    rule_metrics = compute_metrics(y_true, y_rule, conf_rule, "Rule-Based")
    meta_metrics = compute_metrics(y_true, y_meta, conf_meta, "Meta Fusion")

    print("\n" + "=" * 60)
    print("  FUSION COMPARISON RESULTS")
    print("=" * 60)
    fmt = "  {:<24} {:>14} {:>14}"
    print(fmt.format("Metric", "Rule-Based", "Meta Fusion"))
    print("-" * 60)
    for label, rk, mk in [
        ("Accuracy",         "accuracy",         "accuracy"),
        ("Precision (macro)","precision",         "precision"),
        ("Recall (macro)",   "recall",            "recall"),
        ("F1 Score (macro)", "f1",                "f1"),
        ("False Alarm Rate", "false_alarm_rate",  "false_alarm_rate"),
        ("Avg Confidence",   "avg_confidence",    "avg_confidence"),
    ]:
        print(fmt.format(label,
                         f"{rule_metrics[rk]*100:.2f}%",
                         f"{meta_metrics[mk]*100:.2f}%"))
    print("=" * 60)

    out_dir = os.path.join(PROJECT_ROOT, "results", "meta_fusion")
    os.makedirs(out_dir, exist_ok=True)

    comparison = {
        "methodology": (
            "Rule-based uses the raw (unscaled) 32-dim meta-feature vector; "
            "probabilities at per-expert offsets [0,5,10,15,20] are in [0,1]. "
            "Meta fusion uses StandardScaler-transformed features as produced by "
            "train_meta_fusion.py. Both methods evaluated on the same held-out "
            "300-sample test set from meta_fusion_features.npz."
        ),
        "rule_based":  rule_metrics,
        "meta_fusion": meta_metrics,
        "n_test_samples": int(len(y_true)),
    }
    comparison_path = os.path.join(out_dir, "fusion_comparison.json")
    with open(comparison_path, "w") as fh:
        json.dump(comparison, fh, indent=2)
    print(f"[SAVED] Comparison JSON -> {comparison_path}")

    labels      = ["Accuracy", "Precision", "Recall", "F1 Score", "Avg Conf."]
    rule_vals   = [rule_metrics[k] for k in ["accuracy","precision","recall","f1","avg_confidence"]]
    meta_vals   = [meta_metrics[k] for k in ["accuracy","precision","recall","f1","avg_confidence"]]

    x     = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - width/2, [v*100 for v in rule_vals], width,
                   label="Rule-Based", color="#5C7AEA", alpha=0.85)
    bars2 = ax.bar(x + width/2, [v*100 for v in meta_vals], width,
                   label="Meta Fusion", color="#E74C3C", alpha=0.85)
    ax.set_ylabel("Score (%)")
    ax.set_title("Fusion Strategy Comparison on Held-Out Meta Features")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 110)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for bar in list(bars1) + list(bars2):
        ax.annotate(f"{bar.get_height():.1f}",
                    xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    chart_path = os.path.join(out_dir, "fusion_comparison_chart.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] Comparison chart -> {chart_path}")


if __name__ == "__main__":
    main()
