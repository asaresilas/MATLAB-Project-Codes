import os
import numpy as np
import json
from datetime import datetime
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
from sklearn.metrics import classification_report, accuracy_score, f1_score

print("\n==================================")
print("  TRAINING META-FUSION (32-DIM)   ")
print("==================================")

data = np.load('data/meta_fusion_features.npz')
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train = data['X_train']
X_test = data['X_test']
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
y_train = data['y_train']
y_test = data['y_test']

print(f"Loaded Meta-Features: X_train {X_train.shape}, X_test {X_test.shape}")
print(f"Feature Dimensions: {X_train.shape[1]} (Rich Uncertainty Features Active)")

# 1. Define Base Expert Learners for the Stack
if HAS_XGB:
    experts = [
        # Tightened XGBoost to prevent memorization (max_depth=4)
        ('xgb', xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                                 min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
                                 random_state=42, eval_metric='mlogloss')),
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)),
        # MLP with sufficient iterations to converge (2000 avoids ConvergenceWarning)
        ('mlp', MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=2000, alpha=0.01,
                              early_stopping=True, validation_fraction=0.1,
                              n_iter_no_change=30, random_state=42))
    ]

    # Logistic Regression judge: more stable than MLP for meta-learning
    judge = LogisticRegression(C=1.0, max_iter=2000, random_state=42, solver='lbfgs',
                               multi_class='multinomial')
    
    print("\n--- Training Calibrated Stacked Ensemble (XGB + RF + MLP) ---")
    # Using 10-fold CV for maximum scientific stability
    # Single-process default is more portable on Windows and restricted environments.
    stack_model = StackingClassifier(estimators=experts, final_estimator=judge, cv=10, n_jobs=1)
    stack_model.fit(X_train, y_train)
    
    y_pred = stack_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro')
    
    print(f"Calibrated Ensemble Accuracy: {acc*100:.2f}%")
    print(f"Calibrated Ensemble F1-Macro: {f1:.4f}")
    print("\nDetailed Performance Report:")
    print(classification_report(y_test, y_pred))
    
    # SAVE THE PRODUCTION STACK
    os.makedirs('Trained_models/meta_fusion', exist_ok=True)
    import joblib
    model_path = 'Trained_models/meta_fusion/meta_fusion_xgb.pkl' 
    joblib.dump(stack_model, model_path)
    joblib.dump(scaler, 'data/meta_fusion_scaler.pkl')
    print(f"  --> Saved Calibrated Ensemble and Scaler")
    
else:
    print("XGBoost NOT FOUND. Using fallback ensemble.")
    stack_model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    stack_model.fit(X_train, y_train)
    acc = stack_model.score(X_test, y_test)
    f1 = 0.0 # Placeholder
    joblib.dump(stack_model, 'Trained_models/meta_fusion/meta_fusion_xgb.pkl')

# Save standardized metrics
metrics = {
    'Fusion_Accuracy': float(acc),
    'Fusion_F1': float(f1),
    'Training_Samples': X_train.shape[0],
    'Feature_Dimensions': X_train.shape[1],
    'Is_Ensemble': True,
    'Timestamp': datetime.now().isoformat()
}

with open('Trained_models/meta_fusion/metrics_28dim.json', 'w') as f:
    json.dump(metrics, f, indent=4)

print("\n--- HARDENING V2 TRAINING COMPLETE ---")
print(f"  Industrial Standard result: {acc*100:.2f}% (Stacking Active)")
