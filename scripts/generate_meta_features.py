import os
import sys
import numpy as np
import tensorflow as tf
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import sklearn  # noqa: F401
except ImportError:
    print("ERROR: scikit-learn is missing. Please install it using: pip install scikit-learn")
    sys.exit(1)

from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Layer
from tensorflow.keras.utils import custom_object_scope
import tensorflow.keras.backend as K

from src.features.meta_fusion_features import (
    build_nasa_probs,
    ensure_3_classes,
    extract_meta_features_from_predictions,
)


def safe_register(obj):
    try:
        return tf.keras.utils.register_keras_serializable()(obj)
    except Exception:
        return obj


@tf.keras.utils.register_keras_serializable(package="current_feat")
class StatisticsExtractor(tf.keras.layers.Layer):
    """Per-channel amplitude statistics for MCSA slow-sampled current data.
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


@safe_register
class Attention(Layer):
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


@safe_register
def physics_informed_loss(y_true, y_pred):
    return 0.0


print("\n--- Phase 1: Meta-Activation Extraction (Production Data Generator) ---")

if not os.path.exists("data/fusion_train_cache.npz") or not os.path.exists("data/fusion_test_cache.npz"):
    raise FileNotFoundError("Run build_true_dataset.py first to generate the isolated training and testing caches.")

paths = {
    "CWRU": "Trained_models/cwru_cnn/cnn_classifier.keras",  # .keras v3 format (safe_mode compatible)
    "Induction": "Trained_models/induction_dl/best_cnn_model.keras",
    "NASA": "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_model.keras",
    "Current": "Trained_models/current_signature_dl/cnn_model.keras",  # Conv1D CNN, 99.77% acc
    "Thermal": "models/thermal/model.keras",
}

models = {}
for name, path in paths.items():
    if os.path.exists(path):
        print(f"Loading {name} model...")
        try:
            if name == "NASA":
                with custom_object_scope({"physics_informed_loss": physics_informed_loss, "Attention": Attention}):
                    models[name] = load_model(path, compile=False)
            else:
                models[name] = load_model(path, compile=False)
        except Exception as exc:
            print(f"Error loading {name}: {exc}")
    else:
        print(f"[SKIP] {name} — file not found: {path}")

nasa_scaler = None
nasa_scaler_path = "Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl"
if os.path.exists(nasa_scaler_path):
    nasa_scaler = joblib.load(nasa_scaler_path)


def extract_meta_features(cache_path):
    print(f"\nProcessing {cache_path}...")
    cache = np.load(cache_path)

    x_cwru = cache["vibration_cwru"]
    x_ind = cache["vibration_ind"]
    x_nasa = cache["nasa_seq"]
    x_current = cache["current"]
    x_thermal = cache["thermal"]
    y_true = cache["shared_labels"]
    n_samples = len(y_true)

    preds = {}
    preds["CWRU"] = ensure_3_classes(
        models["CWRU"].predict(x_cwru, verbose=0) if "CWRU" in models else np.ones((n_samples, 3)) / 3.0
    )
    preds["Induction"] = ensure_3_classes(
        models["Induction"].predict(x_ind, verbose=0) if "Induction" in models else np.ones((n_samples, 3)) / 3.0
    )
    preds["Current"] = ensure_3_classes(
        models["Current"].predict(x_current, verbose=0) if "Current" in models else np.ones((n_samples, 3)) / 3.0
    )
    preds["Thermal"] = ensure_3_classes(
        models["Thermal"].predict(x_thermal, verbose=0) if "Thermal" in models else np.ones((n_samples, 3)) / 3.0
    )

    if "NASA" in models and nasa_scaler is not None:
        x_nasa_scaled = nasa_scaler.transform(x_nasa.reshape(-1, 36)).reshape(-1, 30, 36)
        ruls = models["NASA"].predict(x_nasa_scaled, verbose=0).flatten()
        preds["NASA"] = build_nasa_probs(ruls)
    else:
        preds["NASA"] = np.ones((n_samples, 3)) / 3.0

    return extract_meta_features_from_predictions(preds), y_true


x_train, y_train = extract_meta_features("data/latent_train_cache.npz")
x_test, y_test = extract_meta_features("data/latent_digital_twin.npz")

os.makedirs("data", exist_ok=True)
np.savez_compressed(
    "data/meta_fusion_features.npz",
    X_train=x_train,
    y_train=y_train,
    X_test=x_test,
    y_test=y_test,
)

print(f"\nPhase 1 Complete. Scientific Features Saved (Dim: {x_train.shape[1]}).")
