import os
import sys
import numpy as np
import tensorflow as tf
import joblib

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("ERROR: scikit-learn is missing. Please install it using: pip install scikit-learn")
    sys.exit(1)

from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Layer
from tensorflow.keras.utils import custom_object_scope
import tensorflow.keras.backend as K

# Robust serialization decorator for different TF/Keras versions
def safe_register(obj):
    try:
        return tf.keras.utils.register_keras_serializable()(obj)
    except Exception:
        return obj

@safe_register
class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)
    def build(self, input_shape):
        self.W = self.add_weight(name='attention_weight', shape=(input_shape[-1], 1), initializer='normal')
        self.b = self.add_weight(name='attention_bias', shape=(input_shape[1], 1), initializer='zeros')
        super(Attention, self).build(input_shape)
    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        return K.sum(x * a, axis=1)

@safe_register
def physics_informed_loss(y_true, y_pred):
    return 0.0

print("\n--- Phase 1: Meta-Activation Extraction (Scientific Benchmark) ---")

# 1. Load the real-world cache
if not os.path.exists('data/fusion_test_cache.npz'):
    raise FileNotFoundError("Run build_true_dataset.py first to generate the cache.")

cache = np.load('data/fusion_test_cache.npz')
X_C = cache['cwru_x']
X_I = cache['ind_x']
X_N = cache['nasa_x']
X_CU = cache['curr_x']
X_T = cache['therm_x']
y_true = cache['cwru_y']  # Unified ground truth labels
N = len(y_true)

print(f"Dataset Loaded. Processing {N} multi-modal samples...")

# 2. Base Model Paths
paths = {
    'CWRU': 'Trained_models/cwru_cnn/cnn_classifier.keras',
    'Induction': 'Trained_models/induction_dl/best_cnn_model.keras',
    'NASA': 'Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_model.keras',
    'Current': 'Trained_models/current_signature_dl/cnn_model.keras',
    'Thermal': 'models/thermal/model.keras'
}

# 3. Load Models
models = {}
for name, p in paths.items():
    if os.path.exists(p):
        print(f"Loading {name} model...")
        try:
            if name == 'NASA':
                with custom_object_scope({'physics_informed_loss': physics_informed_loss, 'Attention': Attention}):
                    models[name] = load_model(p, compile=False)
            else:
                models[name] = load_model(p)
        except Exception as e:
            print(f"Error loading {name}: {e}")

nasa_scaler = joblib.load('Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl') if os.path.exists('Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl') else None

# 4. Generate Activations (Batched for Speed)
print("\nExtracting Activations...")
preds = {}
preds['CWRU'] = models['CWRU'].predict(X_C, verbose=0) if 'CWRU' in models else np.ones((N, 3))/3.0
preds['Induction'] = models['Induction'].predict(X_I, verbose=0) if 'Induction' in models else np.ones((N, 3))/3.0
preds['Current'] = models['Current'].predict(X_CU, verbose=0) if 'Current' in models else np.ones((N, 3))/3.0
preds['Thermal'] = models['Thermal'].predict(X_T, verbose=0) if 'Thermal' in models else np.ones((N, 3))/3.0

nasa_prob = np.ones((N, 3)) / 3.0
if 'NASA' in models and nasa_scaler:
    X_N_flat = X_N.reshape(-1, 36)
    X_N_scaled = nasa_scaler.transform(X_N_flat).reshape(-1, 30, 36)
    ruls = models['NASA'].predict(X_N_scaled, verbose=0).flatten()
    for i, rul in enumerate(ruls):
        p = np.zeros(3)
        if rul > 60: p[0] = 0.8; p[1] = 0.15; p[2] = 0.05
        elif rul > 20: p[0] = 0.1; p[1] = 0.8; p[2] = 0.1
        else: p[0] = 0.05; p[1] = 0.15; p[2] = 0.8
        nasa_prob[i] = p
preds['NASA'] = nasa_prob

# 5. Construct Scientific 28-Dim Feature Vector
print("Building 28-dimensional meta-feature array...")
all_features = []
for i in range(N):
    if i % 100 == 0:
        print(f"  Processed {i}/{N} samples...")
    row = []
    prob_list = []
    
    for mod in ['CWRU', 'Induction', 'NASA', 'Current', 'Thermal']:
        p = np.array(preds[mod][i]).flatten()
        if len(p) < 3:
            p = np.pad(p, (0, 3 - len(p)), mode='constant')
        elif len(p) > 3:
            p = p[:3]
            
        row.extend(p) # 15 dims
        prob_list.append(p)
    
    # Statistical Agreement
    mean_p = np.mean(prob_list, axis=0)
    var_p = np.var(prob_list, axis=0)
    row.extend(mean_p) # 3 dims
    row.extend(var_p) # 3 dims
    
    # Entropy/Uncertainty (One per model)
    for p in prob_list:
        ent = -np.sum(p * np.log(np.clip(p, 1e-7, 1.0)))
        row.append(ent) # 5 dims
        
    # Global Confidence
    max_conf = np.max(mean_p)
    agreement = -np.sum(mean_p * np.log(np.clip(mean_p, 1e-7, 1.0)))
    row.extend([max_conf, agreement]) # 2 dims
    
    all_features.append(row)

X_meta = np.array(all_features)
y_meta = np.array(y_true)

# Split into Train/Test for meta-level evaluation
X_train, X_test, y_train, y_test = train_test_split(X_meta, y_meta, test_size=0.3, random_state=42, stratify=y_meta)

# Standardize
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# 6. Save properly for Phase 2
os.makedirs('data', exist_ok=True)
np.savez_compressed('data/scientific_meta_features.npz', 
                    X_train=X_train_s, y_train=y_train, 
                    X_test=X_test_s, y_test=y_test)
joblib.dump(scaler, 'data/scientific_meta_scaler.pkl')

print(f"\nOK Extraction Complete. Scientific Features Saved.")
print(f"  Shape: {X_train_s.shape} Training samples, {X_test_s.shape} Testing samples.")
