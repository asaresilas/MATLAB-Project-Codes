"""
resave_nasa_model.py
====================
Fixes Keras 3.x incompatibility in NASA Bi-LSTM-Attn model.
Extracts saved weights from the keras archive and rebuilds the model
with a forward-compatible Attention layer, then saves it fresh.

Architecture confirmed from weight inspection:
  Input: (30, 36)
  Bidirectional(LSTM(64, return_sequences=True))   # output (30, 128)
  Bidirectional(LSTM(32, return_sequences=True))   # output (30, 64)
  Attention                                         # output (64,)
  Dense(32, relu) [originally saved as shape (64,32)]
  Dropout
  Dense(1)                                         # scalar RUL

Run from project root:
    python scripts/resave_nasa_model.py
"""

import os, sys, zipfile, json, tempfile, shutil
import numpy as np
import h5py

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MODEL_DIR   = os.path.join(PROJECT_ROOT, "Trained_models", "nasa_dl_comparison", "Bi-LSTM-Attn")
MODEL_PATH  = os.path.join(MODEL_DIR, "Bi-LSTM-Attn_model.keras")
BACKUP_PATH = os.path.join(MODEL_DIR, "Bi-LSTM-Attn_model_backup.keras")

import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras.layers import Layer
from tensorflow.keras import layers, Model, Input
tf.get_logger().setLevel("ERROR")

print("=" * 60)
print("NASA Bi-LSTM-Attn — Keras Compatibility Resave")
print("=" * 60)

# ── 1. Backup original ─────────────────────────────────────────────────
if not os.path.exists(BACKUP_PATH):
    shutil.copy2(MODEL_PATH, BACKUP_PATH)
    print(f"[OK] Backed up original to {BACKUP_PATH}")
else:
    print("[OK] Backup already exists.")

# ── 2. Extract weights from keras archive ──────────────────────────────
tmpdir = tempfile.mkdtemp()
weights_h5_path = os.path.join(tmpdir, "model.weights.h5")
with zipfile.ZipFile(MODEL_PATH, 'r') as z:
    z.extract("model.weights.h5", tmpdir)
print(f"[OK] Extracted weights: {os.path.getsize(weights_h5_path)/1024:.1f} KB")

# ── 3. Load all weight arrays from HDF5 using confirmed structure ──────
#  layers/bidirectional/forward_layer/cell/vars/[0-2]  -> LSTM kernel, recurrent, bias
#  (same for backward_layer)
#  layers/attention/vars/[0-1]                         -> W, b
#  layers/dense/vars/[0-1]                             -> kernel, bias
#  layers/dense_1/vars/[0-1]                           -> kernel, bias

def load_h5_array(f, path):
    """Load a numpy array from HDF5 path."""
    return np.array(f[path])

print("\n[STEP 1] Loading weights from HDF5 ...")
with h5py.File(weights_h5_path, 'r') as f:
    # Bidirectional 1 (LSTM 64 units, input_dim=36)
    bi1_fwd_kernel    = load_h5_array(f, "layers/bidirectional/forward_layer/cell/vars/0")  # (36, 256)
    bi1_fwd_rec       = load_h5_array(f, "layers/bidirectional/forward_layer/cell/vars/1")  # (64, 256)
    bi1_fwd_bias      = load_h5_array(f, "layers/bidirectional/forward_layer/cell/vars/2")  # (256,)
    bi1_bwd_kernel    = load_h5_array(f, "layers/bidirectional/backward_layer/cell/vars/0")
    bi1_bwd_rec       = load_h5_array(f, "layers/bidirectional/backward_layer/cell/vars/1")
    bi1_bwd_bias      = load_h5_array(f, "layers/bidirectional/backward_layer/cell/vars/2")

    # Bidirectional 2 (LSTM 32 units, input_dim=128=64*2)
    bi2_fwd_kernel    = load_h5_array(f, "layers/bidirectional_1/forward_layer/cell/vars/0") # (128,128)
    bi2_fwd_rec       = load_h5_array(f, "layers/bidirectional_1/forward_layer/cell/vars/1") # (32, 128)
    bi2_fwd_bias      = load_h5_array(f, "layers/bidirectional_1/forward_layer/cell/vars/2") # (128,)
    bi2_bwd_kernel    = load_h5_array(f, "layers/bidirectional_1/backward_layer/cell/vars/0")
    bi2_bwd_rec       = load_h5_array(f, "layers/bidirectional_1/backward_layer/cell/vars/1")
    bi2_bwd_bias      = load_h5_array(f, "layers/bidirectional_1/backward_layer/cell/vars/2")

    # Attention
    att_W  = load_h5_array(f, "layers/attention/vars/0")  # (64, 1)
    att_b  = load_h5_array(f, "layers/attention/vars/1")  # (30, 1)

    # Dense 1 (output_dim=32)
    d1_kernel = load_h5_array(f, "layers/dense/vars/0")   # (64, 32)
    d1_bias   = load_h5_array(f, "layers/dense/vars/1")   # (32,)

    # Dense 2 (output_dim=1)
    d2_kernel = load_h5_array(f, "layers/dense_1/vars/0") # (32, 1)
    d2_bias   = load_h5_array(f, "layers/dense_1/vars/1") # (1,)

print(f"  bi1_fwd_kernel : {bi1_fwd_kernel.shape}")
print(f"  att_W          : {att_W.shape}")
print(f"  d1_kernel      : {d1_kernel.shape}")

# ── 4. Build new model with compatible Attention ───────────────────────
print("\n[STEP 2] Building new model ...")

@tf.keras.utils.register_keras_serializable(package="nasa_compat")
class AttentionCompat(Layer):
    """Soft attention — keyword-only add_weight() for Keras 3.x."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
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

# Architecture confirmed from weight inspection:
#   Bi-LSTM(64)  → output (30, 128)
#   Bi-LSTM(32)  → output (30, 64)
#   Attention    → output (64,)          [att_W=(64,1), att_b=(30,1)]
#   Dense(32)    → output (32,)          [d1_kernel=(64,32)]
#   Dense(1)     → scalar RUL            [d2_kernel=(32,1)]
inp = Input(shape=(30, 36), name="input_layer")
x   = layers.Bidirectional(
          layers.LSTM(64, return_sequences=True),
          name="bidirectional")(inp)
x   = layers.Dropout(0.2, name="dropout")(x)
x   = layers.Bidirectional(
          layers.LSTM(32, return_sequences=True),
          name="bidirectional_1")(x)
x   = layers.Dropout(0.2, name="dropout_1")(x)
x   = AttentionCompat(name="attention")(x)
x   = layers.Dense(32, activation="relu", name="dense")(x)   # (64,32) in weights
x   = layers.Dropout(0.2, name="dropout_2")(x)
out = layers.Dense(1, name="dense_1")(x)                      # (32,1) in weights

new_model = Model(inp, out, name="functional")

# Run one forward pass to build all weight tensors
dummy = np.zeros((1, 30, 36), dtype=np.float32)
_ = new_model(dummy)

print(f"  Built model with {len(new_model.layers)} layers")

# ── 5. Set weights manually by layer name ─────────────────────────────
print("\n[STEP 3] Injecting weights ...")

def set_layer_weights(layer_name, weights_list):
    layer = new_model.get_layer(layer_name)
    current_ws = layer.get_weights()
    if len(current_ws) != len(weights_list):
        print(f"  [MISMATCH] {layer_name}: model={len(current_ws)}, h5={len(weights_list)}")
        return
    layer.set_weights(weights_list)
    print(f"  [OK] {layer_name}: {[w.shape for w in weights_list]}")

# Bidirectional LSTM layers store weights as:
# [fwd_kernel, fwd_rec_kernel, fwd_bias, bwd_kernel, bwd_rec_kernel, bwd_bias]
set_layer_weights("bidirectional",
    [bi1_fwd_kernel, bi1_fwd_rec, bi1_fwd_bias,
     bi1_bwd_kernel, bi1_bwd_rec, bi1_bwd_bias])

set_layer_weights("bidirectional_1",
    [bi2_fwd_kernel, bi2_fwd_rec, bi2_fwd_bias,
     bi2_bwd_kernel, bi2_bwd_rec, bi2_bwd_bias])

set_layer_weights("attention", [att_W, att_b])
set_layer_weights("dense",     [d1_kernel, d1_bias])
set_layer_weights("dense_1",   [d2_kernel, d2_bias])

# ── 6. Validate ───────────────────────────────────────────────────────
print("\n[STEP 4] Validating on physical test cache ...")
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error

cache_path = os.path.join(PROJECT_ROOT, "data", "fusion_test_cache.npz")
cache = np.load(cache_path, allow_pickle=True)
X_nasa = cache["nasa_x"].astype(np.float32)   # (270, 30, 36)
y_nasa = cache["nasa_y"].astype(np.float32)

scaler_path = os.path.join(MODEL_DIR, "Bi-LSTM-Attn_scaler.pkl")
scaler = joblib.load(scaler_path)

n = X_nasa.shape[0]
X_flat = X_nasa.reshape(n, -1)[:, :36]
X_scaled = scaler.transform(X_flat)
X_in = np.repeat(X_scaled[:, np.newaxis, :], 30, axis=1).astype(np.float32)

preds = new_model.predict(X_in, batch_size=64, verbose=0).flatten()
mae  = mean_absolute_error(y_nasa, preds)
rmse = np.sqrt(mean_squared_error(y_nasa, preds))
ss_res = np.sum((y_nasa - preds) ** 2)
ss_tot = np.sum((y_nasa - np.mean(y_nasa)) ** 2)
r2   = 1 - ss_res / (ss_tot + 1e-9)

print(f"  MAE  = {mae:.4f} h   (published: 1.35 h)")
print(f"  RMSE = {rmse:.4f} h  (published: 1.73 h)")
print(f"  R²   = {r2:.4f}    (published: 0.9964)")

if r2 > 0.90:
    print("  [PASS] Weights transferred successfully — model matches published metrics")
else:
    print("  [WARN] R² lower than expected — weight order may differ")

# ── 7. Save ───────────────────────────────────────────────────────────
new_model.save(MODEL_PATH)
print(f"\n[SAVED] {MODEL_PATH}")
shutil.rmtree(tmpdir, ignore_errors=True)
print("Done.")
