import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.universal_loader import UniversalDataLoader
from src.models.universal_model import UniversalModelBuilder

def train_universal_model():
    # 1. Configuration
    BASE_DIR = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes"
    MODEL_SAVE_DIR = os.path.join(BASE_DIR, 'Trained_models', 'universal_model')
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
    
    # 2. Load Data
    print("Initializing Universal Data Loader...")
    loader = UniversalDataLoader(BASE_DIR)
    data = loader.prepare_data(split_ratio=(0.7, 0.15, 0.15))
    
    train_data = data['train']
    val_data = data['val']
    
    print(f"Training samples: {len(train_data['labels'])}")
    print(f"Validation samples: {len(val_data['labels'])}")
    
    # 3. Build Model
    print("Building Universal Model...")
    builder = UniversalModelBuilder(num_classes=loader.num_classes)
    model = builder.build_model()
    
    # 4. Compile Model
    # Multi-task losses
    losses = {
        'classification_head': 'categorical_crossentropy',
        'rul_head': 'mse',
        'anomaly_head': 'binary_crossentropy'
    }
    
    loss_weights = {
        'classification_head': 1.0,
        'rul_head': 0.5,
        'anomaly_head': 0.3
    }
    
    metrics = {
        'classification_head': 'accuracy',
        'rul_head': 'mae',
        'anomaly_head': 'AUC'
    }
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss=losses,
        loss_weights=loss_weights,
        metrics=metrics
    )
    
    # 5. Callbacks
    callbacks = [
        EarlyStopping(monitor='val_classification_head_loss', mode='min', patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_classification_head_loss', mode='min', factor=0.5, patience=5, min_lr=1e-6),
        ModelCheckpoint(os.path.join(MODEL_SAVE_DIR, 'best_universal_model.keras'), save_best_only=True)
    ]
    
    # Compute Sample Weights (Robust for multi-output models)
    from sklearn.utils.class_weight import compute_sample_weight
    
    # Convert one-hot to indices
    y_train_indices = np.argmax(train_data['labels'], axis=1)
    
    # Compute sample weights
    sample_weights = compute_sample_weight(class_weight='balanced', y=y_train_indices)
    
    print(f"Sample Weights Shape: {sample_weights.shape}")
    print(f"Sample Weights Example (First 10): {sample_weights[:10]}")

    # 6. Train
    print("Starting Training...")
    history = model.fit(
        x={
            'vibration': train_data['vibration'],
            'current': train_data['current'],
            'tabular': train_data['tabular']
        },
        y=[
            train_data['labels'],      # Output 0: classification_head
            train_data['rul'],          # Output 1: rul_head
            train_data['anomaly']       # Output 2: anomaly_head
        ],
        validation_data=(
            {
                'vibration': val_data['vibration'],
                'current': val_data['current'],
                'tabular': val_data['tabular']
            },
            [
                val_data['labels'],     # Output 0: classification_head
                val_data['rul'],        # Output 1: rul_head
                val_data['anomaly']     # Output 2: anomaly_head
            ]
        ),
        epochs=30, # Initial test run
        batch_size=32,
        callbacks=callbacks,
        # Use LIST format to match the model's output list structure
        sample_weight=[
            sample_weights,                    # For classification_head (balanced)
            np.ones_like(sample_weights),      # For rul_head (equal weight)
            np.ones_like(sample_weights)       # For anomaly_head (equal weight)
        ]
    )
    
    print("Training Complete.")
    
    # Plot training history
    print("\nGenerating training history plots...")
    plot_training_history(history, MODEL_SAVE_DIR)
    
    return history, model

def plot_training_history(history, save_dir):
    """Plot training history with individual graphs for each metric"""
    import matplotlib.pyplot as plt
    
    # Get all metric names
    metrics = [key for key in history.history.keys() if not key.startswith('val_')]
    
    # Plot each metric separately
    for metric in metrics:
        plt.figure(figsize=(10, 6))
        
        # Plot training metric
        plt.plot(history.history[metric], label=f'Training {metric}', linewidth=2)
        
        # Plot validation metric if it exists
        val_metric = f'val_{metric}'
        if val_metric in history.history:
            plt.plot(history.history[val_metric], label=f'Validation {metric}', linewidth=2)
        
        plt.title(f'{metric.replace("_", " ").title()} Over Epochs', fontsize=14, fontweight='bold')
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel(metric.replace('_', ' ').title(), fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Save the plot
        filename = f'{metric}_history.png'
        filepath = os.path.join(save_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()

if __name__ == "__main__":

    train_universal_model()
