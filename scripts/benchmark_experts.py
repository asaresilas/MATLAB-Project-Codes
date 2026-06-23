import os
import sys
import numpy as np
import joblib
from sklearn.metrics import f1_score, classification_report
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import custom_object_scope
import tensorflow as tf
import tensorflow.keras.backend as K

# Registry
class Attention(tf.keras.layers.Layer):
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

def physics_informed_loss(y_true, y_pred): return 0.0

def ensure_3_classes(p):
    if p.shape[1] < 3:
        return np.pad(p, ((0, 0), (0, 3 - p.shape[1])), mode='constant')
    return p[:, :3]

def run_benchmarks():
    print("📋 Phase 2: Benchmarking Individual Modal Experts...")
    
    paths = {
        'CWRU': 'Trained_models/cwru_cnn/cnn_classifier.keras',
        'Induction': 'Trained_models/induction_dl/best_cnn_model.keras',
        'NASA': 'Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_model.keras',
        'Current': 'Trained_models/current_signature_dl/cnn_model.keras',
        'Thermal': 'models/thermal/model.keras'
    }
    
    cache = np.load('data/latent_digital_twin.npz')
    y_true = cache['shared_labels']
    
    modality_data = {
        'CWRU': cache['vibration_cwru'],
        'Induction': cache['vibration_ind'],
        'NASA': cache['nasa_seq'],
        'Current': cache['current'],
        'Thermal': cache['thermal']
    }
    
    nasa_scaler = joblib.load('Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/Bi-LSTM-Attn_scaler.pkl')
    
    for name, p in paths.items():
        if not os.path.exists(p): continue
        print(f"\nAnalyzing Expert: {name}")
        
        with custom_object_scope({'Attention': Attention, 'physics_informed_loss': physics_informed_loss}):
            model = load_model(p, compile=False if name=='NASA' else True)
            
        X = modality_data[name]
        if name == 'NASA':
            X = nasa_scaler.transform(X.reshape(-1, 36)).reshape(-1, 30, 36)
            
        probs = model.predict(X, verbose=0)
        
        if name == 'NASA':
            # RUL to Class mapping for benchmarking purposes
            # (Using the same 0.35/0.75 boundaries as the generator)
            ruls = probs.flatten() / 100.0
            y_pred = np.zeros_like(ruls, dtype=int)
            y_pred[ruls < 0.65] = 1 # Warning
            y_pred[ruls < 0.25] = 2 # Critical
        else:
            probs = ensure_3_classes(probs)
            y_pred = np.argmax(probs, axis=1)
            
        f1 = f1_score(y_true, y_pred, average='macro')
        print(f"  Expert F1-Macro: {f1:.4f}")
        print(classification_report(y_true, y_pred, labels=[0,1,2], target_names=['Healthy', 'Warning', 'Critical']))

if __name__ == "__main__":
    run_benchmarks()
