import joblib
import os
from sklearn.preprocessing import StandardScaler
from app.services.model_registry import registry

# Path to the NASA scaler
scaler_path = os.path.join(os.getcwd(), 'Trained_models', 'nasa_dl_comparison', 'Bi-LSTM-Attn', 'Bi-LSTM-Attn_scaler.pkl')

if os.path.exists(scaler_path):
    print(f"Loading and re-saving scaler at {scaler_path}...")
    try:
        scaler = joblib.load(scaler_path)
        # Re-save with current version
        joblib.dump(scaler, scaler_path)
        print("Success: Scaler updated to scikit-learn 1.5.2")
    except Exception as e:
        print(f"Error checking scaler: {e}")
else:
    print("NASA Scaler not found at expected path.")
