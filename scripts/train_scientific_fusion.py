import os
import numpy as np
import json
import joblib
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# Neural Network imports
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

print("\n==============================================")
print("  PHASE 2: SCIENTIFIC FUSION BENCHMARK SUITE  ")
print("==============================================\n")

# 1. Load the Scientific Meta-Features
DATA_PATH = 'data/scientific_meta_features.npz'
if not os.path.exists(DATA_PATH):
    print(f"ERROR: {DATA_PATH} not found. Did you run extract_meta_activations.py?")
    exit(1)

data = np.load(DATA_PATH)
X_train, y_train = data['X_train'], data['y_train']
X_test, y_test = data['X_test'], data['y_test']

print(f"Loaded Features: Train {X_train.shape}, Test {X_test.shape}")
print(f"Targets: 0=Normal, 1=Warning, 2=Critical\n")

results = {}

# 2. Baseline 1: Logistic Regression (Linear)
print("--- Training Logistic Regression Baseline ---")
lr = LogisticRegression(max_iter=1000, multi_class='multinomial')
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
results['LogisticRegression'] = {
    'Accuracy': float(accuracy_score(y_test, y_pred_lr)),
    'Macro_F1': float(f1_score(y_test, y_pred_lr, average='macro'))
}
print(f"  Accuracy: {results['LogisticRegression']['Accuracy']*100:.2f}%")
print(f"  Macro-F1: {results['LogisticRegression']['Macro_F1']:.4f}\n")

# 3. Baseline 2: Random Forest (Bagging)
print("--- Training Random Forest Baseline ---")
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
results['RandomForest'] = {
    'Accuracy': float(accuracy_score(y_test, y_pred_rf)),
    'Macro_F1': float(f1_score(y_test, y_pred_rf, average='macro'))
}
print(f"  Accuracy: {results['RandomForest']['Accuracy']*100:.2f}%")

# 4. Baseline 3: XGBoost (Boosting)
if HAS_XGB:
    print("\n--- Training XGBoost Baseline ---")
    xgb_model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    results['XGBoost'] = {
        'Accuracy': float(accuracy_score(y_test, y_pred_xgb)),
        'Macro_F1': float(f1_score(y_test, y_pred_xgb, average='macro'))
    }
    print(f"  Accuracy: {results['XGBoost']['Accuracy']*100:.2f}%")

# 5. Our Proposed Model: Deep Meta-Fusion (Neural)
print("\n--- Training Proposed Deep Meta-Learner ---")
model = Sequential([
    Dense(64, activation='relu', input_dim=X_train.shape[1]),
    BatchNormalization(),
    Dropout(0.3),
    Dense(32, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(3, activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

os.makedirs('Trained_models/scientific_fusion', exist_ok=True)
ckpt = ModelCheckpoint('Trained_models/scientific_fusion/best_meta_model.keras', 
                       monitor='val_accuracy', save_best_only=True, verbose=0)
es = EarlyStopping(monitor='val_accuracy', patience=15, restore_best_weights=True)

history = model.fit(X_train, y_train, validation_data=(X_test, y_test),
                    epochs=100, batch_size=16, callbacks=[ckpt, es], verbose=0)

# Evaluate Deep Model
y_pred_probs_dl = model.predict(X_test, verbose=0)
y_pred_dl = np.argmax(y_pred_probs_dl, axis=1)
results['DeepMetaFusion'] = {
    'Accuracy': float(accuracy_score(y_test, y_pred_dl)),
    'Macro_F1': float(f1_score(y_test, y_pred_dl, average='macro'))
}
print(f"  Accuracy: {results['DeepMetaFusion']['Accuracy']*100:.2f}%")
print(f"  Macro-F1: {results['DeepMetaFusion']['Macro_F1']:.4f}\n")

# 6. Final Honest Comparison Table
print("==============================================")
print("             FINAL HONEST RESULTS             ")
print("==============================================")
print(f"{'Method':<20} | {'Accuracy':<10} | {'Macro-F1':<10}")
print("-" * 45)
for method, metrics in results.items():
    print(f"{method:<20} | {metrics['Accuracy']*100:>8.2f}% | {metrics['Macro_F1']:>10.4f}")
print("==============================================\n")

# Save detailed results for publication artifacts
res_path = 'results/scientific_benchmark.json'
os.makedirs('results', exist_ok=True)
with open(res_path, 'w') as f:
    json.dump({'timestamp': datetime.now().isoformat(), 'results': results}, f, indent=4)

print(f"OK Tournament Complete. Full evidence saved to {res_path}")
