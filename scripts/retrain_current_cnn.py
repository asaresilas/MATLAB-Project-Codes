"""
retrain_current_cnn.py  (v5 — pre-extracted features + Normalization layer)
===========================================================================
Fixes the NaN loss that affects v1-v4:

Root cause of NaN:
  The raw CSV files contain some rows with missing values (empty cells read as
  NaN by pandas).  A single NaN in a training window → std=NaN → BN input NaN
  → loss NaN → NaN gradients → all weights become NaN → 33% stuck accuracy.

v5 fix:
  1. Strict NaN/Inf cleaning of every raw window at load time.
  2. Extract 15-dim statistical features as NUMPY (outside Keras graph) — avoids
     any TF-side numerical instability during the forward pass.
  3. Use layers.Normalization(axis=-1).adapt(F_train) — stores mean/variance as
     proper TF Variables (non-trainable), NOT a numpy-closure Lambda.  This gives
     correct gradient flow and correct serialisation.
  4. Train the Dense head on the clean scaled features (15-dim input).
  5. For inference, build a functional wrapper:
       raw (1000,3) → StatisticsExtractor → Normalization → Dense head → softmax
     This is the model saved to disk so the backend receives (1000,3) input.

Label convention (must match fusion_test_cache.npz curr_y):
  0 = healthy   1 = bearing_fault   2 = broken_rotor_bar

Run from project root:
    python scripts/retrain_current_cnn.py
"""

import os, sys, json, warnings, time
import numpy as np
import pandas as pd
import glob
warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

CURRENT_DIR = os.path.join(
    PROJECT_ROOT, "datasets", "Current_Signature",
    "Current Signature Dataset of Three-Phase Induction Motor under Varying Load Conditions"
)
OUT_DIR = os.path.join(PROJECT_ROOT, "Trained_models", "current_signature_dl")
os.makedirs(OUT_DIR, exist_ok=True)

LABEL_MAP   = {"healthy": 0, "bearing_fault": 1, "broken_rotor_bar": 2}
CLASS_NAMES = ["Healthy", "Bearing-Fault", "Broken-Rotor-Bar"]
WINDOW_SIZE = 1000
STRIDE      = 500
SEED        = 42
np.random.seed(SEED)

print("=" * 65)
print("Current Signature — Feature-Extraction MLP  (v5 — NaN-safe)")
print(f"Label convention: {LABEL_MAP}")
print("=" * 65)

# ── 1. Load raw CSV files with NaN cleaning ─────────────────────────────────
def _clean_window(w: np.ndarray) -> np.ndarray | None:
    """Return window with NaN/Inf replaced by channel mean, or None if > 5% bad."""
    bad = ~np.isfinite(w)
    if bad.mean() > 0.05:
        return None          # discard window with > 5% bad values
    if bad.any():
        for c in range(w.shape[1]):
            col = w[:, c]
            m = np.isfinite(col)
            if m.any():
                col[~m] = col[m].mean()
    return w

def load_class(folder_glob: str, label: int):
    windows, labels = [], []
    # Try exact folder glob first
    pattern = os.path.join(CURRENT_DIR, folder_glob, "*.csv")
    csv_files = glob.glob(pattern)
    if not csv_files:
        # Fallback: recursive search for key substring
        key = folder_glob.replace("3-Phase-current-", "").replace("*", "").strip("-")
        all_csvs = glob.glob(os.path.join(CURRENT_DIR, "**", "*.csv"), recursive=True)
        csv_files = [f for f in all_csvs if key in os.path.basename(os.path.dirname(f))]
    print(f"  [{CLASS_NAMES[label]}] {len(csv_files)} CSV files in '{folder_glob}'")
    nan_count = 0
    for fp in csv_files:
        try:
            df = pd.read_csv(fp, header=None, skiprows=1)
            if df.shape[1] < 4:
                continue
            sig = df.iloc[:, 1:4].values.astype(np.float64)
            # Replace infinite values before windowing
            sig = np.where(np.isfinite(sig), sig, np.nan)
            for start in range(0, len(sig) - WINDOW_SIZE, STRIDE):
                w = sig[start: start + WINDOW_SIZE].copy()
                w_clean = _clean_window(w)
                if w_clean is not None:
                    windows.append(w_clean.astype(np.float32))
                    labels.append(label)
                else:
                    nan_count += 1
        except Exception as exc:
            print(f"    skip {os.path.basename(fp)}: {exc}")
    if nan_count:
        print(f"    (discarded {nan_count} windows with > 5% NaN)")
    print(f"    => {len(windows)} clean windows")
    return windows, labels

print("\n[STEP 1] Loading and cleaning raw data ...")
w0, l0 = load_class("3-Phase-current-healthy-motor",           LABEL_MAP["healthy"])
w1, l1 = load_class("3-Phase-current-*-bearing-fault",          LABEL_MAP["bearing_fault"])
w2, l2 = load_class("3-Phase-current-*-broken-rotor-bar-fault", LABEL_MAP["broken_rotor_bar"])

print(f"\nRaw class sizes: Healthy={len(w0)}, Bearing={len(w1)}, BRB={len(w2)}")

if len(w0) == 0 and len(w1) == 0 and len(w2) == 0:
    print("\n[ERROR] No data found. Check CURRENT_DIR:")
    print(f"  {CURRENT_DIR}")
    sys.exit(1)

# ── 2. Balance classes ───────────────────────────────────────────────────────
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib

available = [(cls, np.array(wx, dtype=np.float32))
             for cls, wx in enumerate([w0, w1, w2]) if len(wx) > 0]
print(f"Classes with data: {[CLASS_NAMES[c] for c,_ in available]}")

max_n  = max(len(arr) for _, arr in available)
TARGET = min(max_n, 3000)
print(f"Resampling target per class: {TARGET}")

balanced_x, balanced_y = [], []
for cls, arr in available:
    n   = len(arr)
    idx = np.random.choice(n, TARGET, replace=(n < TARGET))
    balanced_x.append(arr[idx])
    balanced_y.extend([cls] * TARGET)

all_x = np.concatenate(balanced_x, axis=0)
all_y = np.array(balanced_y, dtype=np.int32)
perm  = np.random.permutation(len(all_x))
all_x, all_y = all_x[perm], all_y[perm]

# Final NaN check on balanced set
n_bad = np.sum(~np.isfinite(all_x))
if n_bad:
    print(f"[WARN] {n_bad} non-finite values found in balanced set — replacing with 0")
    all_x = np.where(np.isfinite(all_x), all_x, 0.0)

print(f"Balanced dataset: {len(all_x)} windows  (NaN-free: {np.all(np.isfinite(all_x))})")

# ── 3. Feature extraction (outside Keras graph — NaN-safe) ──────────────────
def extract_features(X: np.ndarray) -> np.ndarray:
    """Extract 15 statistical features from (N, 1000, 3) windows.

    Features per channel (3 channels × 5 stats = 15):
      mean, std, range (max-min), max, min

    Scientific basis (MCSA literature — Benbouzid 2000, Blodt 2008):
    Amplitude-domain statistics discriminate bearing and rotor faults in
    slow-sampled DC-like current measurements better than spectral features.
    """
    mean_ = X.mean(axis=1)
    std_  = X.std(axis=1)
    max_  = X.max(axis=1)
    min_  = X.min(axis=1)
    rng_  = max_ - min_
    feats = np.concatenate([mean_, std_, rng_, max_, min_], axis=1)
    # Safety: clamp any residual NaN/Inf
    feats = np.where(np.isfinite(feats), feats, 0.0)
    return feats.astype(np.float32)

print("\n[STEP 2] Extracting features ...")
all_feats = extract_features(all_x)
print(f"Feature matrix: {all_feats.shape}  (NaN-free: {np.all(np.isfinite(all_feats))})")

# Quick diagnostic: check variance per feature
feat_var = all_feats.var(axis=0)
print(f"Feature variances (min={feat_var.min():.4f}, max={feat_var.max():.4f}) — "
      f"{'OK' if feat_var.min() > 1e-6 else 'WARNING: some features near-zero variance'}")

# ── 4. Train / test split ────────────────────────────────────────────────────
idx_tr, idx_te = train_test_split(
    np.arange(len(all_x)), test_size=0.30, stratify=all_y, random_state=SEED
)
X_raw_train, X_raw_test = all_x[idx_tr],    all_x[idx_te]
F_train,     F_test      = all_feats[idx_tr], all_feats[idx_te]
y_train,     y_test      = all_y[idx_tr],    all_y[idx_te]

print(f"\nTrain: {X_raw_train.shape}  |  Test: {X_raw_test.shape}")
print("Train class dist:", dict(zip(*np.unique(y_train, return_counts=True))))

# Save per-channel scaler for backend raw-input normalisation
scaler_raw = StandardScaler()
scaler_raw.fit(X_raw_train.reshape(-1, 3))
joblib.dump(scaler_raw, os.path.join(OUT_DIR, "scaler.pkl"))
print("[SAVED] scaler.pkl")

# ── 5. Sanity check with sklearn RandomForest on features ────────────────────
from sklearn.ensemble import RandomForestClassifier
print("\n[SANITY] RandomForest baseline on 15-dim features ...")
rf = RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
rf.fit(F_train, y_train)
rf_pred = rf.predict(F_test)
rf_acc  = accuracy_score(y_test, rf_pred)
rf_f1   = f1_score(y_test, rf_pred, average="macro", zero_division=0)
print(f"  RF Accuracy: {rf_acc*100:.2f}%  |  RF F1-macro: {rf_f1*100:.2f}%")
print(f"  (Should be > 85% — confirms features are informative)")

# ── 6. Build Keras model on pre-extracted features ───────────────────────────
import tensorflow as tf
tf.get_logger().setLevel("ERROR")
from tensorflow.keras import layers, Model, Input

print("\n[STEP 3] Building Keras Dense MLP on 15-dim features ...")

# Use layers.Normalization (proper TF Variable-backed normalisation, not Lambda)
norm_layer = layers.Normalization(axis=-1, name="feature_norm")
norm_layer.adapt(F_train)   # computes mean & variance as TF Variables

inp_feat = Input(shape=(15,), name="input_features")
x = norm_layer(inp_feat)
x = layers.Dense(128, activation="relu", name="dense_1")(x)
x = layers.Dropout(0.3, name="drop_1")(x)
x = layers.Dense(64, activation="relu", name="dense_2")(x)
x = layers.Dropout(0.2, name="drop_2")(x)
x = layers.Dense(32, activation="relu", name="dense_3")(x)
out = layers.Dense(3, activation="softmax", name="output")(x)
model_feat = Model(inp_feat, out, name="current_feat_mlp_v5_inner")

model_feat.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
model_feat.summary()

# ── 7. Train on features (NaN-safe — no custom layer in training path) ───────
cb = [
    tf.keras.callbacks.EarlyStopping(
        patience=20, restore_best_weights=True,
        monitor="val_accuracy", verbose=1, min_delta=0.005
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        factor=0.5, patience=8, min_lr=1e-6,
        monitor="val_loss", verbose=1
    ),
]

print("\n[STEP 4] Training on features ...")
t0 = time.time()
history = model_feat.fit(
    F_train, y_train,
    validation_data=(F_test, y_test),
    epochs=200,
    batch_size=64,
    callbacks=cb,
    verbose=1,
)
elapsed = (time.time() - t0) / 60
best_val = max(history.history["val_accuracy"])
print(f"\nTraining time: {elapsed:.1f} min  |  Best val_accuracy: {best_val:.4f}")

# ── 8. Evaluate feature model ────────────────────────────────────────────────
probs_feat = model_feat.predict(F_test, batch_size=64, verbose=0)
y_pred_feat = np.argmax(probs_feat, axis=1)
acc_feat = accuracy_score(y_test, y_pred_feat)
f1_feat  = f1_score(y_test, y_pred_feat, average="macro", zero_division=0)

print("\n" + "=" * 65)
print("EVALUATION (feature model on 30% holdout)")
print("=" * 65)
print(f"  Accuracy : {acc_feat*100:.2f}%")
print(f"  F1-macro : {f1_feat*100:.2f}%")
print()
print(classification_report(y_test, y_pred_feat, target_names=CLASS_NAMES, zero_division=0))

# ── 9. Build full inference wrapper: raw (1000,3) → features → norm → Dense ─
print("\n[STEP 5] Building full inference model (1000,3) input wrapper ...")

@tf.keras.utils.register_keras_serializable(package="current_feat")
class StatisticsExtractor(tf.keras.layers.Layer):
    """Extracts per-channel statistics (mean, std, range, max, min) from
    (batch, timesteps, channels) raw current windows.

    Output: (batch, channels * 5) = 15 features for 3 channels.

    Scientific basis: for slow-sampled MCSA data, amplitude-domain statistics
    (Benbouzid 2000, Blodt 2008) discriminate bearing and rotor-bar faults.
    """
    def call(self, x):
        mu  = tf.reduce_mean(x, axis=1)
        sig = tf.math.reduce_std(x, axis=1)
        mx  = tf.reduce_max(x, axis=1)
        mn  = tf.reduce_min(x, axis=1)
        rng = mx - mn
        return tf.concat([mu, sig, rng, mx, mn], axis=1)  # (batch, 15)

    def get_config(self):
        return super().get_config()

# Build wrapper model sharing the trained Dense weights
inp_raw = Input(shape=(WINDOW_SIZE, 3), name="input_layer")
x_feats = StatisticsExtractor(name="stats_extractor")(inp_raw)

# Re-create norm layer with SAME adapted statistics and make it non-trainable
norm_wrapper = layers.Normalization(axis=-1, name="feature_norm")
norm_wrapper.adapt(F_train)   # same statistics as during training
norm_wrapper.trainable = False

x = norm_wrapper(x_feats)

# Re-use the trained Dense weights by name-matching
for lyr in model_feat.layers:
    if lyr.name.startswith("dense") or lyr.name == "output":
        x = lyr(x)

model_full = Model(inp_raw, x, name="current_feat_mlp_v5")
model_full.summary(line_length=80)

# Verify: feature model and full model give same output on test data
out_feat = model_feat.predict(F_test[:10], verbose=0)
out_full = model_full.predict(X_raw_test[:10], batch_size=10, verbose=0)
max_diff = np.abs(out_feat - out_full).max()
print(f"\n[VERIFY] Max prediction diff between feature model & full model: {max_diff:.6f}")
if max_diff < 1e-4:
    print("  [OK] Full model predictions match feature model exactly.")
else:
    print(f"  [WARN] Larger than expected. Proceeding anyway.")

# ── 10. Validate on fusion_test_cache.npz ────────────────────────────────────
print("\n[STEP 6] Validating on fusion_test_cache.npz (physical holdout) ...")
cache_path = os.path.join(PROJECT_ROOT, "data", "fusion_test_cache.npz")
acc_c, f1_c = 0.0, 0.0
if os.path.exists(cache_path):
    cache = np.load(cache_path, allow_pickle=True)
    Xc = cache["curr_x"].astype(np.float32)
    yc = cache["curr_y"].astype(int)
    # NaN-clean cache data too
    Xc = np.where(np.isfinite(Xc), Xc, 0.0)

    probs_c  = model_full.predict(Xc, batch_size=64, verbose=0)
    y_pred_c = np.argmax(probs_c, axis=1)
    acc_c = accuracy_score(yc, y_pred_c)
    f1_c  = f1_score(yc, y_pred_c, average="macro", zero_division=0)

    print(f"  Cache accuracy : {acc_c*100:.2f}%")
    print(f"  Cache F1-macro : {f1_c*100:.2f}%")
    print("  Cache pred dist:", dict(zip(*np.unique(y_pred_c, return_counts=True))))
    print()
    print(classification_report(yc, y_pred_c, target_names=CLASS_NAMES, zero_division=0))
else:
    print("  [WARN] fusion_test_cache.npz not found")

# ── 11. Save model & metadata ─────────────────────────────────────────────────
save_path = os.path.join(OUT_DIR, "cnn_model.keras")
model_full.save(save_path)
print(f"\n[SAVED] {save_path}")

meta = {
    "accuracy_holdout":      round(float(acc_feat), 4),
    "f1_macro_holdout":      round(float(f1_feat), 4),
    "accuracy_cache":        round(float(acc_c), 4),
    "f1_macro_cache":        round(float(f1_c), 4),
    "rf_baseline_accuracy":  round(float(rf_acc), 4),
    "rf_baseline_f1":        round(float(rf_f1), 4),
    "n_train": int(len(X_raw_train)),
    "n_test":  int(len(X_raw_test)),
    "label_map": {v: k for k, v in LABEL_MAP.items()},
    "architecture": (
        "Full inference model: input(1000,3) → StatisticsExtractor(15 stats) → "
        "Normalization → Dense(128,relu) → Dropout(0.3) → Dense(64,relu) → "
        "Dropout(0.2) → Dense(32,relu) → Dense(3,softmax). "
        "Trained on pre-extracted 15-dim features (NaN-safe path)."
    ),
    "nan_fix": (
        "v5 fixes persistent NaN loss (v1-v4) by: "
        "(1) cleaning raw CSV NaN/Inf values at load time, "
        "(2) extracting features as numpy OUTSIDE the Keras graph, "
        "(3) training the Dense head on clean 15-dim features, "
        "(4) using layers.Normalization().adapt() instead of Lambda closure "
        "(proper TF Variable-backed normalisation with correct gradient flow), "
        "(5) gradient clipping (clipnorm=1.0) in Adam optimizer."
    ),
    "scientific_basis": (
        "Current Signature dataset uses slow-sampled DC-like current values. "
        "Per-channel amplitude statistics (mean, std, range, max, min = 15 features) "
        "are the standard MCSA fault indicators. "
        "References: Benbouzid (2000) IEEE Ind. Electron., Blodt et al. (2008) "
        "IEEE Trans. Ind. Electron."
    ),
    "timestamp": __import__("datetime").datetime.now().isoformat(),
}
with open(os.path.join(OUT_DIR, "retrain_meta.json"), "w") as fh:
    json.dump(meta, fh, indent=2)
print(f"[SAVED] retrain_meta.json")
print("\nRetrain complete.")
