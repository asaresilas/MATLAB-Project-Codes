import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models, applications
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import classification_report
import json

# Constants - Paths relative to project root
DATA_DIR = r"datasets/Thermal"
MODELS_DIR = r"models/thermal"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20 # reduced for faster check, but transfer learning converges fast
SEED = 42

print(f"TensorFlow Version: {tf.__version__}")
print(f"Data Directory: {os.path.abspath(DATA_DIR)}")

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)

import shutil
from sklearn.model_selection import train_test_split

print("Enforcing strict directory-based stratified split...")
train_dir = os.path.join(DATA_DIR, "train")
val_dir = os.path.join(DATA_DIR, "val")
test_dir = os.path.join(DATA_DIR, "test")

# Reorganize if not already split
if not os.path.exists(train_dir):
    print("Partitioning dataset into train/val/test directories...")
    classes = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    
    for cls in classes:
        cls_dir = os.path.join(DATA_DIR, cls)
        images = [f for f in os.listdir(cls_dir) if f.casefold().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        if len(images) > 0:
            # Stratified split: 70% train, 15% val, 15% test
            train_imgs, temp_imgs = train_test_split(images, test_size=0.3, random_state=SEED)
            val_imgs, test_imgs = train_test_split(temp_imgs, test_size=0.5, random_state=SEED)
            
            for split_name, imgs in [("train", train_imgs), ("val", val_imgs), ("test", test_imgs)]:
                split_cls_dir = os.path.join(DATA_DIR, split_name, cls)
                os.makedirs(split_cls_dir, exist_ok=True)
                for img in imgs:
                    shutil.move(os.path.join(cls_dir, img), os.path.join(split_cls_dir, img))
                    
        # Optional: remove original empty class dir
        # if not os.listdir(cls_dir): os.rmdir(cls_dir)

print("Loading dataset from strict directories...")
try:
    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels='inferred',
        label_mode='categorical',
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=SEED
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir,
        labels='inferred',
        label_mode='categorical',
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
        seed=SEED
    )
    
    test_ds = tf.keras.utils.image_dataset_from_directory(
        test_dir,
        labels='inferred',
        label_mode='categorical',
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
        seed=SEED
    )
except Exception as e:
    print(f"Error loading dataset: {e}")
    exit(1)

class_names = train_ds.class_names
print(f"\nClasses ({len(class_names)}): {class_names}")

# Optimization
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
test_ds = test_ds.prefetch(buffer_size=AUTOTUNE)

# Data Augmentation (Aggressive for small dataset)
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.2),
    layers.RandomContrast(0.2),
    layers.RandomBrightness(0.2),
])

# Model Architecture (EfficientNetB0)
print("Building Improved Model (EfficientNetB0)...")
base_model = applications.EfficientNetB0(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')
base_model.trainable = False

inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
x = data_augmentation(inputs)
x = applications.efficientnet.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dropout(0.4)(x)
outputs = layers.Dense(len(class_names), activation='softmax')(x)

model = models.Model(inputs, outputs)
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Callbacks
checkpoint_path = os.path.join(MODELS_DIR, "model.keras")
callbacks = [
    ModelCheckpoint(checkpoint_path, save_best_only=True, monitor='val_accuracy', mode='max', verbose=1),
    EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1)
]

# Training
print("Starting initial training...")
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=50,
    callbacks=callbacks
)

# Fine-Tuning
print("Starting fine-tuning (Unfreezing top 50 layers)...")
base_model.trainable = True
for layer in base_model.layers[:-50]:
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

history_fine = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=30,
    callbacks=callbacks
)

# Evaluation
print("Evaluating model...")
loss, acc = model.evaluate(test_ds)
print(f"Test Accuracy: {acc*100:.2f}%")

# Generate Classification Report
print("Generating classification report...")
y_true = []
y_pred = []

for images, labels in test_ds:
    preds = model.predict(images, verbose=0)
    y_true.extend(np.argmax(labels.numpy(), axis=1))
    y_pred.extend(np.argmax(preds, axis=1))

print(classification_report(y_true, y_pred, target_names=class_names, labels=range(len(class_names)), zero_division=0))

# Save Metadata
metadata = {
    "class_names": class_names,
    "image_size": list(IMG_SIZE)
}
with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved.")
