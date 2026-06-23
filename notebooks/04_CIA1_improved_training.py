import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers, Model, Input
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.layers import Add, Multiply, Dense, Dropout, BatchNormalization, Concatenate

# Add project root to path
sys.path.append(r'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes')
from src.data.loaders import CIA1Loader

print("="*80)
print("IMPROVED TRAINING PIPELINE: Fixing Leakage & Saving Best Models")
print("="*80)

# 1. Load Data
data_dir = os.path.join(r'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes', 'datasets', 'CIA-1')
loader = CIA1Loader(data_dir)
X, y, feature_names = loader.load_data()
class_names = loader.get_class_names()

# 2. Split Data: Train (60%), Validation (20%), Test (20%)
# First split: Train+Val (80%) and Test (20%)
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Second split: Train (75% of 80% = 60%) and Val (25% of 80% = 20%)
X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val
)

print(f"Data Split Shapes:")
print(f"  Train (Original): {X_train.shape}")
print(f"  Validation:       {X_val.shape}")
print(f"  Test:             {X_test.shape}")

# 3. Apply SMOTE ONLY to Training Data
print("\nApplying SMOTE to Training Data only...")
smote = SMOTE(random_state=42, k_neighbors=3)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
print(f"  Balanced Train:   {X_train_balanced.shape}")

# 4. Scale Data
# Fit scaler on Balanced Training Data (or just Training Data)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_balanced)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Convert labels to categorical
y_train_cat = to_categorical(y_train_balanced, num_classes=4)
y_val_cat = to_categorical(y_val, num_classes=4)
y_test_cat = to_categorical(y_test, num_classes=4)

# 5. Model Definitions
def build_mlp(input_dim, num_classes):
    model = keras.Sequential([
        layers.Dense(128, activation='relu', input_shape=(input_dim,)),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_deep_mlp(input_dim, num_classes):
    model = keras.Sequential([
        layers.Dense(256, activation='relu', input_shape=(input_dim,)),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_1d_cnn(input_dim, num_classes):
    inputs = Input(shape=(input_dim, 1))
    x = layers.Conv1D(32, 3, activation='relu', padding='same')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Conv1D(64, 3, activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Flatten()(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_attention_mlp(input_dim, num_classes):
    inputs = Input(shape=(input_dim,))
    x = Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001))(inputs)
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)
    attention = Dense(128, activation='tanh')(x)
    attention = Dense(128, activation='softmax')(attention)
    x = Multiply()([x, attention])
    x = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001))(x)
    x = BatchNormalization()(x)
    x = Dropout(0.3)(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=keras.optimizers.Adam(0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_ensemble_nn(input_dim, num_classes, n_models=3):
    inputs = Input(shape=(input_dim,))
    branches = []
    for i in range(n_models):
        branch = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001))(inputs)
        branch = BatchNormalization()(branch)
        branch = Dropout(0.4)(branch)
        branch = Dense(32, activation='relu')(branch)
        branch = Dropout(0.3)(branch)
        branches.append(branch)
    combined = Concatenate()(branches)
    x = Dense(64, activation='relu')(combined)
    x = Dropout(0.3)(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=keras.optimizers.Adam(0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_tabnet_inspired(input_dim, num_classes):
    inputs = Input(shape=(input_dim,))
    x = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001))(inputs)
    x = BatchNormalization()(x)
    attention = Dense(input_dim, activation='softmax')(x)
    attended_features = Multiply()([inputs, attention])
    x = Concatenate()([x, attended_features])
    x = Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001))(x)
    x = BatchNormalization()(x)
    x = Dropout(0.4)(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.3)(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=keras.optimizers.Adam(0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def build_autoencoder_classifier(input_dim, num_classes):
    inputs = Input(shape=(input_dim,))
    encoded = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.001))(inputs)
    encoded = BatchNormalization()(encoded)
    encoded = Dropout(0.3)(encoded)
    encoded = Dense(32, activation='relu')(encoded)
    decoded = Dense(64, activation='relu')(encoded)
    decoded = Dense(input_dim, activation='linear')(decoded)
    x = Dense(64, activation='relu')(encoded)
    x = Dropout(0.3)(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=keras.optimizers.Adam(0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

# 6. Train Models
input_dim = X_train_scaled.shape[1]
num_classes = 4
models = {
    'MLP': build_mlp(input_dim, num_classes),
    'Deep_MLP': build_deep_mlp(input_dim, num_classes),
    '1D_CNN': build_1d_cnn(input_dim, num_classes),
    'Attention_MLP': build_attention_mlp(input_dim, num_classes),
    'Ensemble_NN': build_ensemble_nn(input_dim, num_classes),
    'TabNet_Inspired': build_tabnet_inspired(input_dim, num_classes),
    'Autoencoder_Classifier': build_autoencoder_classifier(input_dim, num_classes)
}

results = {}
save_dir = r'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\models'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

for name, model in models.items():
    print(f'\nTRAINING {name}...')
    
    # Prepare inputs
    if name == '1D_CNN':
        X_train_in = X_train_scaled.reshape(-1, X_train_scaled.shape[1], 1)
        X_val_in = X_val_scaled.reshape(-1, X_val_scaled.shape[1], 1)
        X_test_in = X_test_scaled.reshape(-1, X_test_scaled.shape[1], 1)
    else:
        X_train_in = X_train_scaled
        X_val_in = X_val_scaled
        X_test_in = X_test_scaled
        
    # Callbacks
    checkpoint_path = os.path.join(save_dir, f'best_model_{name}.keras')
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
        ModelCheckpoint(filepath=checkpoint_path, monitor='val_accuracy', save_best_only=True, mode='max', verbose=0)
    ]
    
    # Train
    history = model.fit(
        X_train_in, y_train_cat,
        validation_data=(X_val_in, y_val_cat),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
        verbose=0 # Reduce verbosity for summary
    )
    
    # Evaluate
    loss, acc = model.evaluate(X_test_in, y_test_cat, verbose=0)
    print(f'  Test Accuracy: {acc:.4f}')
    
    # Detailed Report
    y_pred = model.predict(X_test_in, verbose=0)
    y_pred_classes = np.argmax(y_pred, axis=1)
    print(classification_report(y_test, y_pred_classes, target_names=class_names, zero_division=0))
    
    results[name] = acc

print("\n" + "="*60)
print("FINAL IMPROVED RESULTS")
print("="*60)
for name, acc in results.items():
    print(f"{name:25s}: {acc:.4f}")

best_model_name = max(results, key=results.get)
print(f"\nBest Model: {best_model_name} with {results[best_model_name]:.4f} accuracy")
print(f"Best model saved to: {os.path.join(save_dir, 'best_model_' + best_model_name + '.keras')}")
