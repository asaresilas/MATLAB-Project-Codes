import json
import os

notebook_path = 'notebooks/07_Thermal_Imaging_Training.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Helper to find cells by content substring
def find_cell(substring):
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and any(substring in line for line in cell['source']):
            return i
    return -1

# 1. Update Architecture and Augmentation
arch_idx = find_cell('applications.MobileNetV2')
if arch_idx != -1:
    new_source = [
        "# Data Augmentation (Aggressive for small dataset)\n",
        "data_augmentation = tf.keras.Sequential([\n",
        "    layers.RandomFlip(\"horizontal_and_vertical\"),\n",
        "    layers.RandomRotation(0.2),\n",
        "    layers.RandomZoom(0.2),\n",
        "    layers.RandomContrast(0.2),\n",
        "    layers.RandomBrightness(0.2), # New: Brightness\n",
        "])\n",
        "\n",
        "# Base Model: Switching to EfficientNetB0 for better performance\n",
        "base_model = applications.EfficientNetB0(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')\n",
        "base_model.trainable = False # Freeze base model initially\n",
        "\n",
        "# Full Model\n",
        "inputs = tf.keras.Input(shape=IMG_SIZE + (3,))\n",
        "x = data_augmentation(inputs)\n",
        "# EfficientNetB0 expects [0, 255] or handles its own scaling, but we'll use its specific preprocessor\n",
        "x = applications.efficientnet.preprocess_input(x)\n",
        "x = base_model(x, training=False)\n",
        "x = layers.GlobalAveragePooling2D()(x)\n",
        "x = layers.BatchNormalization()(x) # Added BatchNormalization\n",
        "x = layers.Dropout(0.4)(x) # Increased Dropout\n",
        "outputs = layers.Dense(len(class_names), activation='softmax')(x)\n",
        "\n",
        "model = models.Model(inputs, outputs)\n",
        "\n",
        "model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),\n",
        "              loss='categorical_crossentropy',\n",
        "              metrics=['accuracy'])\n",
        "\n",
        "model.summary()\n"
    ]
    nb['cells'][arch_idx]['source'] = new_source

# 2. Update Fine-Tuning
ft_idx = find_cell('base_model.trainable = True')
if ft_idx != -1:
    new_source = [
        "base_model.trainable = True\n",
        "\n",
        "# Freeze all layers except the last 50 (MobileNetV2 had ~150, EfficientNetB0 has ~230)\n",
        "for layer in base_model.layers[:-50]:\n",
        "    layer.trainable = False\n",
        "\n",
        "model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5), # Very low LR for fine-tuning\n",
        "              loss='categorical_crossentropy',\n",
        "              metrics=['accuracy'])\n",
        "\n",
        "# Increase epochs for fine-tuning to 30\n",
        "history_fine = model.fit(\n",
        "    train_ds,\n",
        "    validation_data=val_ds,\n",
        "    epochs=30,\n",
        "    callbacks=callbacks\n",
        ")\n"
    ]
    nb['cells'][ft_idx]['source'] = new_source

# 3. Update Global Epochs
config_idx = find_cell('EPOCHS =')
if config_idx != -1:
    source = nb['cells'][config_idx]['source']
    for i, line in enumerate(source):
        if 'EPOCHS =' in line:
            source[i] = "    EPOCHS = 50\n" # Back to 50 for initial training
    nb['cells'][config_idx]['source'] = source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4)

print(f"Improved {notebook_path} with EfficientNetB0 and stronger augmentation.")
