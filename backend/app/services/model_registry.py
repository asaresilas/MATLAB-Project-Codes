"""
Model Registry — Singleton that loads and exposes all Keras/pickle models.

The custom Attention layer and accuracy metric are defined at module level so
they are not re-created on every call to load_models().
"""

import os
import logging
import joblib
import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras.layers import Layer
from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Custom Keras objects (must be module-level so they are not redefined) ──────

@tf.keras.utils.register_keras_serializable(package="motorguard")
class Attention(Layer):
    """Bahdanau-style additive attention used by the NASA Bi-LSTM model.

    Keras-3.x compatible: uses keyword-only shape argument in add_weight()
    to avoid the positional 'shape' conflict introduced in Keras 3.
    Registered as a serialisable custom object so the model can be saved
    and reloaded across sessions without extra custom_objects dicts.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
        # keyword-only 'shape' to avoid Keras 3.x positional-arg conflict
        self.W = self.add_weight(
            name="attention_weight",
            shape=(int(input_shape[-1]), 1),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.b = self.add_weight(
            name="attention_bias",
            shape=(int(input_shape[1]), 1),
            initializer="zeros",
            trainable=True,
        )
        super().build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        return K.sum(x * a, axis=1)

    def get_config(self):
        return super().get_config()

    @classmethod
    def from_config(cls, config):
        return cls(**config)


def accuracy_10_percent(y_true, y_pred):
    """Custom metric: fraction of predictions within ±10 h of the true RUL."""
    diff = K.abs(y_true - y_pred)
    return K.mean(K.less_equal(diff, 10.0))


@tf.keras.utils.register_keras_serializable(package="current_feat")
class StatisticsExtractor(tf.keras.layers.Layer):
    """Per-channel amplitude statistics for MCSA slow-sampled current data.

    Extracts (mean, std, range, max, min) per channel from (batch, T, C) input.
    Output: (batch, C * 5) = 15 features for 3 channels.

    Scientific basis: For Motor Current Signature Analysis (MCSA) with slow-
    sampled DC-like current data, amplitude-domain statistics discriminate
    bearing and rotor-bar faults (Benbouzid 2000, Blodt 2008).
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


_CUSTOM_OBJECTS = {
    "Attention": Attention,
    "accuracy_10_percent": accuracy_10_percent,
    "StatisticsExtractor": StatisticsExtractor,
}


# ── Registry singleton ─────────────────────────────────────────────────────────

class ModelRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.models = {}
            cls._instance.scalers = {}
            cls._instance.configs = {}
            cls._instance._load_summary = {}   # per-model load outcome for /health
        return cls._instance

    # ── Loading ────────────────────────────────────────────────────────────────

    def load_models(self):
        """Load every model listed in deployment_config.json."""
        logger.info("ModelRegistry: loading models …")
        logger.debug("BASE_DIR  = %s", settings.BASE_DIR)
        logger.debug("CONFIG    = %s", settings.CONFIG_PATH)

        try:
            deployment_config = settings.load_deployment_config()
        except Exception as exc:
            logger.error("Failed to read deployment_config.json: %s", exc)
            return

        logger.info("Config contains %d dataset(s)", len(deployment_config))

        for dataset_name, config in deployment_config.items():
            if config.get("model_type") != "keras":
                logger.error("  [SKIP] %s — unsupported model_type '%s'",
                             dataset_name, config.get("model_type"))
                self._load_summary[dataset_name] = "unsupported_type"
                continue

            model_path = os.path.join(settings.BASE_DIR, config["model_path"])
            if not os.path.exists(model_path):
                logger.warning("  [SKIP] %s — file not found: %s", dataset_name, model_path)
                self._load_summary[dataset_name] = "file_not_found"
                continue

            try:
                self._load_single(dataset_name, model_path, config)
            except Exception as exc:
                logger.error("  [ERROR] %s — %s", dataset_name, exc)
                self._load_summary[dataset_name] = f"error: {exc}"

        loaded = list(self.models.keys())
        logger.info("ModelRegistry ready — %d model(s) loaded: %s", len(loaded), loaded)

    def _load_single(self, name: str, path: str, config: dict):
        """Load one Keras model; handles both safe (.keras) and legacy (.h5) formats."""
        is_legacy = config.get("legacy_format", False)

        if is_legacy:
            logger.warning(
                "  [SECURITY] %s uses legacy HDF5 format — loading with safe_mode=False. "
                "Convert to .keras v3 format to eliminate this risk.",
                name,
            )
            model = tf.keras.models.load_model(
                path,
                custom_objects=_CUSTOM_OBJECTS,
                compile=False,
                safe_mode=False,   # explicitly acknowledged for legacy files only
            )
        else:
            model = tf.keras.models.load_model(
                path,
                custom_objects=_CUSTOM_OBJECTS,
                compile=False,
                safe_mode=True,
            )

        self.models[name] = model
        self.configs[name] = config
        logger.info("  [OK] %s loaded", name)

        # Optional scaler
        scaler_rel = config.get("scaler_path")
        if scaler_rel:
            scaler_path = os.path.join(settings.BASE_DIR, scaler_rel)
            if os.path.exists(scaler_path):
                self.scalers[name] = joblib.load(scaler_path)
                logger.info("  [OK] %s scaler loaded", name)
            else:
                logger.warning("  [SKIP] %s scaler not found: %s", name, scaler_path)

        self._load_summary[name] = "loaded"

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_loaded(self) -> bool:
        return bool(self.models)

    def get_model(self, model_id: str):
        return self.models.get(model_id)

    def get_scaler(self, dataset_name: str):
        return self.scalers.get(dataset_name)

    def get_model_info(self, dataset_name: str):
        return self.configs.get(dataset_name)

    def health_detail(self) -> dict:
        """Return per-model load status — used by /health/detailed."""
        return {
            "models_loaded": len(self.models),
            "models_expected": len(self._load_summary),
            "per_model": {
                name: {
                    "status": self._load_summary.get(name, "not_attempted"),
                    "loaded": name in self.models,
                    "description": self.configs.get(name, {}).get("description", ""),
                }
                for name in set(list(self._load_summary.keys()) + list(self.models.keys()))
            },
        }


# Global singleton
registry = ModelRegistry()
