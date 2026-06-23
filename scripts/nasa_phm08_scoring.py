"""
nasa_phm08_scoring.py -- NASA C-MAPSS / PHM08 standard RUL evaluation.

Implements the asymmetric scoring function defined in:
  Saxena, A. & Goebel, K. (2008). C-MAPSS Data Set.
  NASA Ames Prognostics Data Repository.

The PHM08 score penalises late predictions (positive error) more harshly than
early predictions (negative error):

  s_i = exp(-RUL_true_i / 13) - 1   if  error_i < 0  (early prediction)
  s_i = exp( RUL_true_i / 10) - 1   if  error_i >= 0 (late prediction)

  where error_i = RUL_pred_i - RUL_true_i
  Score = sum(s_i)

NOTE: This framework uses the NASA IMS bearing dataset (run-to-failure vibration),
NOT the turbofan C-MAPSS dataset. The RUL scale is therefore in HOURS (100->0),
not in CYCLES. The PHM08 formula is adapted with the same asymmetric penalty
structure but the conventional C-MAPSS 'cycles' unit is replaced by 'hours'.

For a rigorous comparison to turbofan-specific literature, a true C-MAPSS
training/test set would be required (FD001-FD004). This script documents what
comparison IS possible with the current bearing dataset.

Run from project root: python scripts/nasa_phm08_scoring.py
Output: results/publication_metrics/nasa_phm08_scoring.json
"""
import os
import sys
import json
import numpy as np
import joblib
from datetime import datetime

import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras.layers import Layer
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import custom_object_scope

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class Attention(Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name="attention_weight", shape=(int(input_shape[-1]), 1),
                                 initializer="normal", trainable=True)
        self.b = self.add_weight(name="attention_bias", shape=(int(input_shape[1]), 1),
                                 initializer="zeros", trainable=True)
        super().build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        return K.sum(x * a, axis=1)


def physics_informed_loss(y_true, y_pred):
    return 0.0


# ?? PHM08-style asymmetric scoring function ???????????????????????????????????

def phm08_score(y_true, y_pred, early_scale=13.0, late_scale=10.0):
    """
    Asymmetric score from Saxena & Goebel (2008), adapted for bearing-hours RUL.
    Positive error (late prediction) is penalised more harshly than negative (early).

    Parameters
    ----------
    y_true       : array-like, true RUL values in hours
    y_pred       : array-like, predicted RUL values in hours
    early_scale  : time constant for early predictions (default 13, per PHM08)
    late_scale   : time constant for late predictions (default 10, per PHM08)

    Returns
    -------
    total_score  : float  (lower is better)
    per_sample   : ndarray of per-sample score contributions
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    error  = y_pred - y_true     # positive = late, negative = early

    per_sample = np.where(
        error < 0,
        np.exp(-error / early_scale) - 1.0,   # early: less penalised
        np.exp( error / late_scale)  - 1.0,   # late:  more penalised
    )
    return float(per_sample.sum()), per_sample


def normalised_rmse(y_true, y_pred, max_rul=None):
    """NRMSE = RMSE / max_RUL (dimensionless)."""
    rmse = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
    if max_rul is None:
        max_rul = float(np.max(np.abs(y_true)))
    return rmse / max_rul if max_rul > 0 else float("nan")


def run_phm08_scoring():
    print("\n=== NASA RUL Evaluation -- PHM08-Style Scoring ===\n")

    # Load NASA Bi-LSTM model
    model_path  = os.path.join(
        PROJECT_ROOT, "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_model.keras")
    scaler_path = os.path.join(
        PROJECT_ROOT, "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl")

    if not os.path.exists(model_path):
        print(f"ERROR: NASA model not found at {model_path}.")
        sys.exit(1)

    print("Loading NASA Bi-LSTM-Attn model ...")
    with custom_object_scope({"Attention": Attention,
                              "physics_informed_loss": physics_informed_loss}):
        model = load_model(model_path, compile=False)

    nasa_scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

    # Load test data (latent DT test set -- 300 samples with RUL in hours)
    dt_path = os.path.join(PROJECT_ROOT, "data/latent_digital_twin.npz")
    if not os.path.exists(dt_path):
        print(f"ERROR: {dt_path} not found. Run build_latent_digital_twin.py first.")
        sys.exit(1)

    cache     = np.load(dt_path)
    x_nasa    = cache["nasa_seq"]      # (300, 30, 36) pre-extracted feature sequences
    y_true    = cache["shared_rul"]    # (300,) true RUL in hours [0, 100]

    print(f"Test set: n={len(y_true)}, RUL range [{y_true.min():.1f}, {y_true.max():.1f}] h")

    # Inference
    if nasa_scaler is not None:
        x_scaled = nasa_scaler.transform(x_nasa.reshape(-1, 36)).reshape(-1, 30, 36)
    else:
        x_scaled = x_nasa
        print("WARNING: Scaler not found -- using unscaled NASA features.")

    y_pred = model.predict(x_scaled, verbose=0).flatten()

    # ?? Standard regression metrics ???????????????????????????????????????????
    mae    = float(np.mean(np.abs(y_pred - y_true)))
    rmse   = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
    ss_res = float(np.sum((y_pred - y_true) ** 2))
    ss_tot = float(np.sum((y_true  - y_true.mean()) ** 2))
    r2     = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    max_rul = float(y_true.max())
    nrmse  = normalised_rmse(y_true, y_pred, max_rul)

    # ?? PHM08-style asymmetric score ??????????????????????????????????????????
    total_score, per_sample_scores = phm08_score(y_true, y_pred)
    n_late  = int(np.sum(y_pred > y_true))
    n_early = int(np.sum(y_pred <= y_true))

    print(f"\n  Standard Metrics:")
    print(f"    MAE   = {mae:.4f} h")
    print(f"    RMSE  = {rmse:.4f} h")
    print(f"    NRMSE = {nrmse:.4f}  (RMSE / max_RUL = {rmse:.4f}/{max_rul:.1f})")
    print(f"    R^2    = {r2:.4f}")
    print(f"\n  PHM08-style Asymmetric Score:")
    print(f"    Total score = {total_score:.2f}  (lower = better)")
    print(f"    n_late  (penalised more): {n_late}")
    print(f"    n_early (penalised less): {n_early}")

    # ?? Comparison context ????????????????????????????????????????????????????
    print("\n  Published C-MAPSS benchmarks for context (different dataset):")
    benchmarks = [
        ("Zheng et al. 2017, LSTM (FD001)",     12.60, 18.60, "cycles"),
        ("Li et al. 2018, CNN (FD001)",           6.80, 12.65, "cycles"),
        ("Attention BiLSTM survey avg (FD001)",   7.47, 12.10, "cycles"),
    ]
    print(f"    {'Method':<42} {'MAE':>8} {'RMSE':>8} {'Unit':>8}")
    for name, mae_b, rmse_b, unit in benchmarks:
        print(f"    {name:<42} {mae_b:>8.2f} {rmse_b:>8.2f} {unit:>8}")
    print(f"    {'This work (IMS bearing, not turbofan)':<42} {mae:>8.2f} {rmse:>8.2f} {'hours':>8}")

    # Save
    out_path = os.path.join(PROJECT_ROOT, "results/publication_metrics/nasa_phm08_scoring.json")
    output   = {
        "methodology": (
            "Evaluated on 300-sample latent DT test set. "
            "RUL in HOURS (IMS bearing, design: RUL = 100*(1-d)). "
            "PHM08 asymmetric score adapted from Saxena & Goebel (2008). "
            "Note: this is not the turbofan C-MAPSS dataset -- direct comparison "
            "to published C-MAPSS benchmarks requires dataset parity."
        ),
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "mae_hours":   round(mae,   4),
            "rmse_hours":  round(rmse,  4),
            "nrmse":       round(nrmse, 4),
            "r2":          round(r2,    4),
            "max_rul_hours": round(max_rul, 2),
        },
        "phm08_score": {
            "total_score":  round(total_score, 2),
            "n_late":  n_late,
            "n_early": n_early,
            "early_penalty_scale": 13.0,
            "late_penalty_scale":  10.0,
            "interpretation": "Lower is better. Late predictions penalised ~1.3x more.",
        },
        "paper_guidance": {
            "unit_correction": "Report MAE/RMSE in hours, NOT in percent.",
            "nrmse_if_reported": f"NRMSE = {nrmse:.4f} = RMSE({rmse:.3f}h) / max_RUL({max_rul:.1f}h)",
            "dataset_clarification": (
                "This project uses the NASA IMS bearing dataset (run-to-failure vibration, "
                "4 bearings, ~1 week duration), NOT the turbofan C-MAPSS dataset. "
                "Direct numerical comparison to C-MAPSS published results (Zheng 2017, "
                "Li 2018) would require matching datasets. Acknowledge this limitation "
                "in the paper or replace with IMS-specific literature comparisons."
            ),
            "comparison_to_add": (
                "Add IMS-specific baselines: Lei et al. 2016 (PRONOSTIA), "
                "Qian et al. 2018 (bearing LSTM), or compare against the "
                "per-model Bi-LSTM result (MAE=1.354h, RMSE=1.734h) as the "
                "single-model baseline."
            ),
        },
        "published_cmapss_benchmarks_context": [
            {"method": n, "mae": m, "rmse": r, "unit": u}
            for n, m, r, u in benchmarks
        ],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\nOK NASA PHM08 scoring saved -> {out_path}")
    return output


if __name__ == "__main__":
    run_phm08_scoring()
