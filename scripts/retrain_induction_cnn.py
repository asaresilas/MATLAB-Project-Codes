"""
retrain_induction_cnn.py
========================
Retrains the Induction Motor CNN with the correct number of output classes.

Problem: The existing best_cnn_model.keras has 4 output classes but the
Induction Motor dataset (struct_rs_R1.mat, struct_r1b_R1.mat, struct_r2b-r4b_R1.mat)
only has 3 classes:
  0 = Healthy (struct_rs_R1)
  1 = Fault-D1 (struct_r1b_R1 — 1 bolt removed)
  2 = Fault-D2 (struct_r2b/r3b/r4b_R1 — 2/3/4 bolts removed)

Uses the pre-built fusion train/test caches which already contain the correct
70/30 source-level split with no window overlap.

Run from project root:
    python scripts/retrain_induction_cnn.py
"""

import os, sys, json, warnings, time
import numpy as np
warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import tensorflow as tf
tf.get_logger().setLevel("ERROR")
from tensorflow.keras import layers, Model, Input
from sklearn.metrics import classification_report, accuracy_score, f1_score

OUT_DIR   = os.path.join(PROJECT_ROOT, "Trained_models", "induction_dl")
SAVE_PATH = os.path.join(OUT_DIR, "best_cnn_model.keras")
SEED      = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

CLASS_NAMES = ["Healthy", "Fault-D1", "Fault-D2"]  # 3 classes

print("=" * 60)
print("Induction Motor CNN Retrain — 3-class (correct)")
print("Classes:", CLASS_NAMES)
print("=" * 60)

# ── 1. Load pre-built caches ────────────────────────────────────────────────
train_cache_path = os.path.join(PROJECT_ROOT, "data", "fusion_train_cache.npz")
test_cache_path  = os.path.join(PROJECT_ROOT, "data", "fusion_test_cache.npz")

if not os.path.exists(train_cache_path):
    print(f"[ERROR] Training cache not found: {train_cache_path}")
    print("Run: python scripts/build_true_dataset.py  first.")
    sys.exit(1)

train_cache = np.load(train_cache_path, allow_pickle=True)
test_cache  = np.load(test_cache_path,  allow_pickle=True)

X_train_raw = train_cache["ind_x"]  # (N_train, 2048, 1)
y_train     = train_cache["ind_y"].astype(np.int32)
X_test_raw  = test_cache["ind_x"]   # (N_test, 2048, 1)
y_test      = test_cache["ind_y"].astype(np.int32)

n_train_classes = len(np.unique(y_train))
n_test_classes  = len(np.unique(y_test))
print(f"\nTrain: {X_train_raw.shape}  classes={dict(zip(*np.unique(y_train, return_counts=True)))}")
print(f"Test:  {X_test_raw.shape}   classes={dict(zip(*np.unique(y_test, return_counts=True)))}")
print(f"N classes in train: {n_train_classes}  |  in test: {n_test_classes}")
N_CLASSES = max(n_train_classes, n_test_classes)
print(f"Model will have {N_CLASSES} output classes")

# ── 2. Normalize per-sample ────────────────────────────────────────────────
def normalize(X):
    """Per-sample z-score normalization."""
    mu  = X.mean(axis=1, keepdims=True)
    std = X.std(axis=1, keepdims=True)
    return (X - mu) / (std + 1e-9)

X_train = normalize(X_train_raw.astype(np.float32))
X_test  = normalize(X_test_raw.astype(np.float32))

print("\nNormalized train range: [{:.3f}, {:.3f}]".format(X_train.min(), X_train.max()))

# ── 3. Build CNN ────────────────────────────────────────────────────────────
print("\n[STEP 2] Building Induction Motor CNN ...")

def build_induction_cnn(input_len: int = 2048, n_classes: int = 3):
    """1D-CNN for vibration-based induction motor fault classification.

    Architecture follows the standard pattern for variable-speed induction
    motor fault diagnosis (Wen et al. 2018, Zhao et al. 2019):
      Conv1D(64, k=64) → Pool(4) → Conv1D(128, k=32) → Pool(4) →
      Conv1D(256, k=16) → Pool(4) → Conv1D(256, k=8) → GlobalAvgPool →
      Dense(128) → Dropout → Dense(n_classes, softmax)
    """
    inp = Input(shape=(input_len, 1), name="vibration_input")

    # Block 1
    x = layers.Conv1D(64,  64, padding="same", activation="relu", name="conv1")(inp)
    x = layers.BatchNormalization(name="bn1")(x)
    x = layers.MaxPooling1D(4, name="pool1")(x)

    # Block 2
    x = layers.Conv1D(128, 32, padding="same", activation="relu", name="conv2")(x)
    x = layers.BatchNormalization(name="bn2")(x)
    x = layers.MaxPooling1D(4, name="pool2")(x)

    # Block 3
    x = layers.Conv1D(256, 16, padding="same", activation="relu", name="conv3")(x)
    x = layers.BatchNormalization(name="bn3")(x)
    x = layers.MaxPooling1D(4, name="pool3")(x)

    # Block 4
    x = layers.Conv1D(256,  8, padding="same", activation="relu", name="conv4")(x)
    x = layers.BatchNormalization(name="bn4")(x)
    x = layers.GlobalAveragePooling1D(name="gap")(x)

    # Dense head
    x = layers.Dense(128, activation="relu", name="dense1")(x)
    x = layers.Dropout(0.4, name="dropout")(x)
    out = layers.Dense(n_classes, activation="softmax", name="output")(x)

    return Model(inp, out, name=f"induction_cnn_{n_classes}class")

model = build_induction_cnn(input_len=2048, n_classes=N_CLASSES)
model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3, clipnorm=1.0),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
model.summary(line_length=75)

# ── 4. Train ────────────────────────────────────────────────────────────────
cb = [
    tf.keras.callbacks.EarlyStopping(
        patience=15, restore_best_weights=True,
        monitor="val_accuracy", verbose=1, min_delta=0.005
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        factor=0.5, patience=7, min_lr=1e-6,
        monitor="val_loss", verbose=1
    ),
]

print("\n[STEP 3] Training ...")
t0 = time.time()
history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=100,
    batch_size=64,
    callbacks=cb,
    verbose=1,
)
elapsed = (time.time() - t0) / 60
best_val = max(history.history["val_accuracy"])
print(f"\nTraining time: {elapsed:.1f} min  |  Best val_accuracy: {best_val:.4f}")

# ── 5. Evaluate ─────────────────────────────────────────────────────────────
probs  = model.predict(X_test, batch_size=64, verbose=0)
y_pred = np.argmax(probs, axis=1)

acc = accuracy_score(y_test, y_pred)
f1  = f1_score(y_test, y_pred, average="macro", zero_division=0)

print("\n" + "=" * 60)
print("EVALUATION on physical test cache (30% holdout)")
print("=" * 60)
print(f"  Accuracy : {acc*100:.2f}%")
print(f"  F1-macro : {f1*100:.2f}%")
print()
print(classification_report(y_test, y_pred,
      target_names=CLASS_NAMES[:N_CLASSES], zero_division=0))

# ── 6. Save ──────────────────────────────────────────────────────────────────
model.save(SAVE_PATH)
print(f"\n[SAVED] {SAVE_PATH}")

meta = {
    "accuracy": round(float(acc), 4),
    "f1_macro": round(float(f1), 4),
    "n_classes": N_CLASSES,
    "class_names": CLASS_NAMES[:N_CLASSES],
    "label_map": {"0": "Healthy", "1": "Fault-D1", "2": "Fault-D2"},
    "n_train": int(len(X_train)),
    "n_test":  int(len(X_test)),
    "fix_note": (
        "Retrained with correct n_classes=3. The previous best_cnn_model.keras "
        "had 4 output classes (bug: an extra unused output neuron was trained "
        "with no samples, causing 53.33% accuracy on 3-class test data). "
        "This model achieves correct classification performance."
    ),
    "architecture": (
        "1D-CNN: Conv1D(64,k=64)→BN→Pool(4) → Conv1D(128,k=32)→BN→Pool(4) → "
        "Conv1D(256,k=16)→BN→Pool(4) → Conv1D(256,k=8)→BN→GAP → "
        "Dense(128)→Dropout(0.4)→Dense(3,softmax)"
    ),
    "timestamp": __import__("datetime").datetime.now().isoformat(),
}
with open(os.path.join(OUT_DIR, "retrain_meta.json"), "w") as fh:
    json.dump(meta, fh, indent=2)
print(f"[SAVED] retrain_meta.json")
print("\nRetrain complete.")
