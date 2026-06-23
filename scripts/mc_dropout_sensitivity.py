"""
mc_dropout_sensitivity.py -- Monte Carlo Dropout T-sensitivity analysis.

Evaluates Expected Calibration Error (ECE) and uncertainty quality for the
Shannon entropy baseline (current system: n_iter=1, deterministic) and for
MC Dropout at T in {5, 10, 20, 30, 50} stochastic forward passes.

NOTE: MC Dropout requires Dropout layers in the model. If the loaded base models
do not have Dropout layers, the script falls back to Shannon entropy only and
documents this clearly for the paper's uncertainty section.

The script also computes:
  - ECE (15 bins) for the meta-fusion model's probability outputs
  - Shannon entropy distribution and the Indeterminate threshold theta
  - Precision-vs-recall tradeoff vs. entropy threshold theta

Run from project root: python scripts/mc_dropout_sensitivity.py
Output: results/publication_metrics/uncertainty_analysis.json
"""
import os
import sys
import json
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score
from datetime import datetime

import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras.layers import Layer
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import custom_object_scope

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.features.meta_fusion_features import (
    build_nasa_probs,
    ensure_3_classes,
    extract_meta_features_from_predictions,
)


class Attention(Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight("attention_weight", shape=(input_shape[-1], 1),
                                 initializer="normal")
        self.b = self.add_weight("attention_bias", shape=(input_shape[1], 1),
                                 initializer="zeros")
        super().build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        return K.sum(x * a, axis=1)


def physics_informed_loss(y_true, y_pred):
    return 0.0


# ?? Uncertainty helpers ????????????????????????????????????????????????????????

def shannon_entropy(probs):
    """Shannon entropy in nats. probs: (n, C) array."""
    p = np.clip(probs, 1e-9, 1.0)
    return float(-np.sum(p * np.log(p), axis=1).mean()) if probs.ndim > 1 else \
           float(-np.sum(probs * np.log(np.clip(probs, 1e-9, 1.0))))


def shannon_entropy_per_sample(probs):
    """Returns (n,) array of Shannon entropy in nats."""
    p = np.clip(probs, 1e-9, 1.0)
    return -np.sum(p * np.log(p), axis=1)


def expected_calibration_error(y_true, y_probs, n_bins=15):
    """
    ECE computed using confidence (max probability) binning.
    Lower is better. Perfect calibration gives ECE = 0.
    """
    confidences = np.max(y_probs, axis=1)
    predictions = np.argmax(y_probs, axis=1)
    correct     = (predictions == y_true).astype(float)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n   = len(y_true)
    bin_details = []

    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (confidences > lo) & (confidences <= hi)
        if mask.sum() == 0:
            bin_details.append(None)
            continue
        bin_acc  = correct[mask].mean()
        bin_conf = confidences[mask].mean()
        bin_n    = int(mask.sum())
        ece     += (bin_n / n) * abs(bin_acc - bin_conf)
        bin_details.append({
            "range": [round(lo, 3), round(hi, 3)],
            "n": bin_n,
            "accuracy": round(float(bin_acc), 4),
            "confidence": round(float(bin_conf), 4),
            "gap": round(float(abs(bin_acc - bin_conf)), 4),
        })

    return float(ece), bin_details


def check_model_has_dropout(model):
    """Returns True if the model contains any Dropout layers."""
    for layer in model.layers:
        if "dropout" in layer.__class__.__name__.lower():
            return True
    return False


def mc_dropout_predict(model, x, n_iter=30):
    """
    Run T stochastic forward passes with training=True to activate Dropout.
    Returns mean and variance of class probabilities across T passes.
    """
    preds = np.stack(
        [model(x, training=True).numpy() for _ in range(n_iter)],
        axis=0
    )   # shape: (T, n_samples, n_classes)
    return preds.mean(axis=0), preds.var(axis=0)


def precision_recall_vs_theta(y_true, y_probs, thetas):
    """
    For each entropy threshold theta: samples with H > theta are flagged 'Indeterminate'.
    Returns precision and recall on the CERTAIN subset (H <= theta).
    """
    entropies = shannon_entropy_per_sample(y_probs)
    results   = []
    for theta in thetas:
        certain_mask = entropies <= theta
        n_certain    = int(certain_mask.sum())
        n_total      = len(y_true)
        if n_certain == 0:
            results.append({"theta": theta, "n_certain": 0, "coverage": 0.0,
                            "f1_certain": None, "accuracy_certain": None})
            continue
        f1_c  = float(f1_score(y_true[certain_mask], np.argmax(y_probs[certain_mask], axis=1),
                               average="macro", zero_division=0))
        acc_c = float(accuracy_score(y_true[certain_mask],
                                     np.argmax(y_probs[certain_mask], axis=1)))
        results.append({
            "theta":            round(float(theta), 3),
            "n_certain":        n_certain,
            "coverage":         round(n_certain / n_total, 4),
            "f1_certain":       round(f1_c,  4),
            "accuracy_certain": round(acc_c, 4),
        })
    return results


# ?? Main analysis ??????????????????????????????????????????????????????????????

def run_uncertainty_analysis():
    print("\n=== Uncertainty Quantification Analysis ===\n")

    # Load meta-features (pre-computed from base models)
    feat_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_features.npz")
    if not os.path.exists(feat_path):
        print(f"ERROR: {feat_path} not found.\nRun scripts/generate_meta_features.py first.")
        sys.exit(1)

    data       = np.load(feat_path)
    X_test_raw = data["X_test"]    # 300 x 32
    y_test     = data["y_test"]

    # Load meta-model and scaler
    meta_model_path  = os.path.join(PROJECT_ROOT, "Trained_models/meta_fusion/meta_fusion_xgb.pkl")
    meta_scaler_path = os.path.join(PROJECT_ROOT, "data/meta_fusion_scaler.pkl")

    if not os.path.exists(meta_model_path):
        print(f"ERROR: {meta_model_path} not found.")
        sys.exit(1)

    meta_model  = joblib.load(meta_model_path)
    meta_scaler = joblib.load(meta_scaler_path) if os.path.exists(meta_scaler_path) else None

    if meta_scaler:
        X_test_s = meta_scaler.transform(X_test_raw)
    else:
        X_test_s = X_test_raw

    # ?? Shannon Entropy baseline (current system, n_iter=1) ??
    print("--- Baseline: Shannon Entropy (n_iter=1, deterministic) ---")
    y_probs     = meta_model.predict_proba(X_test_s)
    y_pred      = meta_model.predict(X_test_s)
    entropies   = shannon_entropy_per_sample(y_probs)
    f1_base     = float(f1_score(y_test, y_pred, average="macro"))
    ece_base, ece_bins = expected_calibration_error(y_test, y_probs)

    print(f"  F1-macro: {f1_base:.4f}")
    print(f"  ECE (15 bins): {ece_base:.4f}")
    print(f"  Mean entropy: {entropies.mean():.4f} nats  (max possible: {np.log(3):.4f} nats)")
    print(f"  Entropy range: [{entropies.min():.4f}, {entropies.max():.4f}]")

    # theta sensitivity analysis
    thetas     = np.linspace(0.05, 1.2, 24)
    theta_analysis = precision_recall_vs_theta(y_test, y_probs, thetas)
    # Find theta that gives >= 99% accuracy on the certain subset with >= 50% coverage
    best_theta = None
    for row in theta_analysis:
        if row["accuracy_certain"] is not None and row["accuracy_certain"] >= 0.99 \
                and row["coverage"] >= 0.50:
            best_theta = row["theta"]
            break

    print(f"  Recommended theta (>=99% acc, >=50% coverage): "
          f"{best_theta if best_theta else 'not found in sweep'}")

    # ?? MC Dropout analysis ??
    mc_results = {}
    mc_possible = False

    # Load one of the Keras base models to check for Dropout
    cwru_path = os.path.join(PROJECT_ROOT, "Trained_models/cwru_cnn/cnn_classifier.keras")
    if os.path.exists(cwru_path):
        print("\n--- Checking for Dropout layers in base models ---")
        with custom_object_scope({"Attention": Attention,
                                  "physics_informed_loss": physics_informed_loss}):
            try:
                sample_model = load_model(cwru_path, compile=False)
                has_dropout  = check_model_has_dropout(sample_model)
                print(f"  CWRU model has Dropout layers: {has_dropout}")
                mc_possible  = has_dropout
            except Exception as e:
                print(f"  Could not load CWRU model: {e}")
                mc_possible = False
    else:
        print("\n  CWRU model file not found -- MC Dropout check skipped.")

    if mc_possible:
        print("\n--- MC Dropout T sensitivity (on CWRU CNN softmax output) ---")
        # Load test data for CWRU
        dt_path = os.path.join(PROJECT_ROOT, "data/latent_digital_twin.npz")
        if os.path.exists(dt_path):
            cache  = np.load(dt_path)
            x_cwru = cache["vibration_cwru"]
            y_cwru = cache["shared_labels"]

            with custom_object_scope({"Attention": Attention,
                                      "physics_informed_loss": physics_informed_loss}):
                cwru_model = load_model(cwru_path, compile=False)

            for T in [5, 10, 20, 30, 50]:
                print(f"  T={T} ...", end=" ", flush=True)
                try:
                    mean_probs, var_probs = mc_dropout_predict(cwru_model, x_cwru, n_iter=T)
                    mean_probs_3 = ensure_3_classes(mean_probs)
                    ece_T, _     = expected_calibration_error(y_cwru, mean_probs_3)
                    f1_T         = float(f1_score(y_cwru, np.argmax(mean_probs_3, axis=1),
                                                  average="macro"))
                    mc_results[f"T={T}"] = {
                        "T":       T,
                        "ece":     round(ece_T, 4),
                        "f1":      round(f1_T,  4),
                        "mean_predictive_variance": round(float(var_probs.mean()), 6),
                    }
                    print(f"ECE={ece_T:.4f}, F1={f1_T:.4f}")
                except Exception as e:
                    print(f"FAILED: {e}")
                    mc_results[f"T={T}"] = {"error": str(e)}
        else:
            print("  latent_digital_twin.npz not found -- MC Dropout evaluation skipped.")
    else:
        print(
            "\n  MC Dropout CANNOT be applied: base models do not have Dropout layers. "
            "\n  Recommendation for paper: document Shannon entropy as the uncertainty method. "
            "\n  If MC Dropout is desired, add Dropout(0.3) layers to base model architectures "
            "\n  and retrain before evaluating T sensitivity."
        )

    # Save
    output = {
        "methodology": (
            "Uncertainty via Shannon entropy H(p) = -sum(p_i * log(p_i)) over the "
            "3-class meta-fusion softmax output. ECE computed with 15 equal-width "
            "confidence bins. MC Dropout requires Dropout layers in base model; "
            "if absent, Shannon entropy is the only uncertainty method implemented."
        ),
        "timestamp":     datetime.now().isoformat(),
        "shannon_entropy_baseline": {
            "n_iter":        1,
            "deterministic": True,
            "f1_macro":      round(f1_base, 4),
            "ece_15bins":    round(ece_base, 4),
            "entropy_mean":  round(float(entropies.mean()), 4),
            "entropy_std":   round(float(entropies.std()),  4),
            "entropy_min":   round(float(entropies.min()),  4),
            "entropy_max":   round(float(entropies.max()),  4),
            "max_possible_entropy_nats": round(float(np.log(3)), 4),
            "ece_bin_details": ece_bins,
        },
        "theta_sensitivity": theta_analysis,
        "recommended_theta": best_theta,
        "mc_dropout_possible": mc_possible,
        "mc_dropout_results":  mc_results if mc_results else None,
        "paper_guidance": {
            "if_mc_dropout_not_possible": (
                "Remove any MC Dropout mentions from the paper. "
                "Document the actual method: Shannon entropy H(p) applied to the "
                "meta-fusion softmax output. Define threshold theta empirically from "
                "the theta_sensitivity sweep above."
            ),
            "uncertainty_method_statement": (
                "Predictive uncertainty is quantified via Shannon entropy "
                "H(p) = -sum_{i} p_i ln(p_i) applied to the meta-fusion probability "
                "vector p in R^3. When H(p) exceeds threshold theta (determined empirically "
                "from a precision-coverage sweep), the system outputs 'Indeterminate' "
                "and escalates to human review."
            ),
        },
    }

    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/uncertainty_analysis.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK Uncertainty analysis saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_uncertainty_analysis()
