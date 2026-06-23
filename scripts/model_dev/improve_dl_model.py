"""
Improve 06_Induction_Motor_DL_training.ipynb model for better accuracy
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Improve CNN Model Architecture
model_improved = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def build_cnn_model(input_shape, num_classes):" in source:
            # Replace entire model definition with improved version
            new_model = """def build_cnn_model(input_shape, num_classes):
    \"\"\"Improved CNN model with deeper architecture for better accuracy.\"\"\"
    model = Sequential([
        # First Conv Block
        Conv1D(filters=64, kernel_size=5, activation='relu', padding='same', input_shape=input_shape),
        BatchNormalization(),
        Conv1D(filters=64, kernel_size=5, activation='relu', padding='same'),
        MaxPooling1D(pool_size=2),
        Dropout(0.2),
        
        # Second Conv Block
        Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'),
        MaxPooling1D(pool_size=2),
        Dropout(0.2),
        
        # Third Conv Block
        Conv1D(filters=256, kernel_size=3, activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),
        
        # Global pooling and classification
        tf.keras.layers.GlobalAveragePooling1D(),
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(num_classes, activation='softmax')
    ])
    
    # Use Adam with learning rate schedule
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])
    return model

input_shape = (X_train.shape[1], X_train.shape[2]) # Fixed: Use actual number of channels from data
num_classes = y_categorical.shape[1]

cnn_model = build_cnn_model(input_shape, num_classes)
cnn_model.summary()
"""
            cell['source'] = new_model.split('\n')
            model_improved = True
            break

if model_improved:
    print("Improved CNN model architecture (deeper, better regularization).")
else:
    print("Warning: Could not find CNN model to improve.")

# 2. Increase training epochs and add early stopping
training_improved = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "history_cnn = cnn_model.fit(" in source:
            # Replace training configuration
            new_training = """# Train CNN with improved configuration
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Callbacks for better training
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1)

history_cnn = cnn_model.fit(
    X_train, y_train,
    epochs=50,  # Increased from 20
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)
"""
            cell['source'] = new_training.split('\n')
            training_improved = True
            break

if training_improved:
    print("Improved training configuration (50 epochs, early stopping, LR scheduling).")
else:
    print("Warning: Could not find training code to improve.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("\nNotebook saved with improvements.")
print("\nExpected improvements:")
print("  - Deeper network (3 conv blocks instead of 2)")
print("  - Better regularization (BatchNorm + reduced dropout)")
print("  - More training epochs (50 with early stopping)")
print("  - Learning rate scheduling")
print("\nExpected accuracy: 75-85% (up from 60%)")
