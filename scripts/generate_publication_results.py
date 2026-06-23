import os
import json
import asyncio
import time
import sys
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
import tensorflow.keras.backend as K
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import label_binarize
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


class Attention(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.add_weight(name="attention_weight", shape=(input_shape[-1], 1), initializer="normal")
        self.b = self.add_weight(name="attention_bias", shape=(input_shape[1], 1), initializer="zeros")
        super(Attention, self).build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        return K.sum(x * a, axis=1)


def physics_informed_loss(y_true, y_pred):
    return 0.0


@tf.keras.utils.register_keras_serializable(package="current_feat")
class StatisticsExtractor(tf.keras.layers.Layer):
    """Per-channel amplitude statistics for MCSA current data.
    Extracts (mean, std, range, max, min) per channel from (batch, T, C) input.
    Output: (batch, C * 5) = 15 features for 3 channels.
    """
    def call(self, x):
        mu  = tf.reduce_mean(x, axis=1)
        sig = tf.math.reduce_std(x, axis=1)
        mx  = tf.reduce_max(x, axis=1)
        mn  = tf.reduce_min(x, axis=1)
        rng = mx - mn
        return tf.concat([mu, sig, rng, mx, mn], axis=1)

    def get_config(self):
        return super().get_config()


def get_expert_predictions(modality_data, models, nasa_scaler):
    preds = {}
    preds["CWRU"] = ensure_3_classes(models["CWRU"].predict(modality_data["vibration_cwru"], verbose=0))
    preds["Induction"] = ensure_3_classes(models["Induction"].predict(modality_data["vibration_ind"], verbose=0))
    preds["Current"] = ensure_3_classes(models["Current"].predict(modality_data["current"], verbose=0))
    preds["Thermal"] = ensure_3_classes(models["Thermal"].predict(modality_data["thermal"], verbose=0))

    x_nasa = modality_data["nasa_seq"]
    x_nasa_scaled = nasa_scaler.transform(x_nasa.reshape(-1, 36)).reshape(-1, 30, 36)
    ruls = models["NASA"].predict(x_nasa_scaled, verbose=0).flatten()
    preds["NASA"] = build_nasa_probs(ruls)
    return preds, ruls


async def run_evaluation():
    print("Initializing Grounded Publication Evaluation...")

    paths = {
        "CWRU": "Trained_models/cwru_cnn/cnn_classifier.keras",  # .keras v3 format
        "Induction": "Trained_models/induction_dl/best_cnn_model.keras",
        "NASA": "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_model.keras",
        "Current": "Trained_models/current_signature_dl/cnn_model.keras",  # Conv1D, 99.77% acc
        "Thermal": "models/thermal/model.keras",
    }

    models = {}
    for name, path in paths.items():
        if os.path.exists(path):
            try:
                if name == "NASA":
                    with custom_object_scope({"Attention": Attention, "physics_informed_loss": physics_informed_loss}):
                        models[name] = load_model(path, compile=False)
                else:
                    models[name] = load_model(path, compile=False)
                print(f"  [OK] {name} loaded")
            except Exception as exc:
                print(f"  [FAIL] {name}: {exc}")

    nasa_scaler = joblib.load("Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl")
    meta_model = joblib.load("Trained_models/meta_fusion/meta_fusion_xgb.pkl")
    meta_scaler = joblib.load("data/meta_fusion_scaler.pkl")

    cache = np.load("data/latent_digital_twin.npz")
    y_true = cache["shared_labels"]
    modality_data = {
        "vibration_cwru": cache["vibration_cwru"],
        "vibration_ind": cache["vibration_ind"],
        "nasa_seq": cache["nasa_seq"],
        "current": cache["current"],
        "thermal": cache["thermal"],
    }

    print("Extracting Rich Meta-Features from Latent State...")
    preds, ruls = get_expert_predictions(modality_data, models, nasa_scaler)
    x_meta = extract_meta_features_from_predictions(preds)
    x_meta_s = meta_scaler.transform(x_meta)

    print("Running Meta-Fusion Inference...")
    latencies = []
    y_pred_list = []
    y_probs_list = []

    for i in range(len(x_meta_s)):
        start = time.perf_counter()
        sample = x_meta_s[i : i + 1]
        pred = meta_model.predict(sample)
        probs = meta_model.predict_proba(sample)
        end = time.perf_counter()

        latencies.append((end - start) * 1000.0)
        y_pred_list.append(pred[0])
        y_probs_list.append(probs[0])

    y_pred = np.array(y_pred_list)
    y_probs = np.array(y_probs_list)

    f1 = f1_score(y_true, y_pred, average="macro")
    report = classification_report(y_true, y_pred, output_dict=True)
    cm = confusion_matrix(y_true, y_pred)
    y_true_bin = label_binarize(y_true, classes=[0, 1, 2])
    macro_auc_ovr = roc_auc_score(y_true_bin, y_probs, multi_class="ovr", average="macro")

    p50_lat = np.percentile(latencies, 50)
    p99_lat = np.percentile(latencies, 99)

    # --- 3. RESTORE RUL EVALUATION (Grounded Maintenance Metrics) ---
    y_true_rul = cache['shared_rul']
    # NASA ruls are already calculated in get_expert_predictions
    y_pred_rul = ruls # Using NASA expert's raw RUL prediction for grounding
    
    mae_rul = mean_absolute_error(y_true_rul, y_pred_rul)
    rmse_rul = np.sqrt(mean_squared_error(y_true_rul, y_pred_rul))
    
    print(f"\nFINAL GROUNDED F1: {f1:.4f}")
    print(f"RUL PERFORMANCE: MAE={mae_rul:.2f} h, RMSE={rmse_rul:.2f} h")
    print(f"Meta-Fusion Stack Latency (XGBoost only): P50={p50_lat:.2f}ms, P99={p99_lat:.2f}ms")
    print(f"NOTE: Full single-sample pipeline ~1050ms (see latency_breakdown.json for breakdown)")

    # Save Results
    results = {
        "f1": float(f1),
        "roc_auc_ovr_macro": float(macro_auc_ovr),
        "rul_mae": float(mae_rul),
        "rul_rmse": float(rmse_rul),
        "confusion_matrix": cm.tolist(),
        "report": report,
        "latency": {
            "p50": float(p50_lat),
            "p99": float(p99_lat),
            "note": "Meta-fusion XGBoost stack only (not full pipeline). Full single-sample pipeline ~1050ms CPU."
        },
        "timestamp": datetime.now().isoformat()
    }
    
    os.makedirs('results/publication_metrics', exist_ok=True)
    with open('results/publication_metrics/official_results.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    # Save RAW data for Figure Generation (Scientific Grounding)
    np.savez_compressed('results/publication_metrics/raw_eval_data.npz', 
                        y_true=y_true, y_pred=y_pred, y_probs=y_probs, 
                        y_true_rul=y_true_rul, y_pred_rul=y_pred_rul,
                        latencies=np.array(latencies))

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Meta-Fusion Confusion Matrix")
    plt.tight_layout()
    plt.savefig("results/publication_metrics/confusion_matrix.png", dpi=200)
    plt.close()

    print("\nEvaluation Complete. Results and raw data saved.")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
