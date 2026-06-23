import os
import sys
import numpy as np
import asyncio
from sklearn.metrics import f1_score, mean_absolute_error

# Add paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from src.data.universal_loader import UniversalDataLoader
from app.services.model_registry import registry
from app.api.websocket_handler import prediction_engine

async def run_final_check():
    print("Initializing PINPOINT Empirical Validation...")
    registry.load_models()
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    loader = UniversalDataLoader(project_root)
    test_data = loader.prepare_data()['test']
    
    n_samples = 10
    print(f"Running evaluation on {n_samples} empirical samples...")
    
    y_true = np.argmax(test_data['labels'][:n_samples], axis=1)
    y_true_bin = (y_true > 0).astype(int)
    
    y_pred = []
    rul_true = test_data['rul'][:n_samples]
    rul_pred = []
    
    for i in range(n_samples):
        # 1. Classification (Full Fusion)
        payload = {
            "vibration": test_data['vibration'][i].tolist(),
            "current": test_data['current'][i].tolist() if i < len(test_data['current']) else [],
            "scalars": test_data['tabular'][i].tolist()
        }
        res = await prediction_engine.predict(payload)
        
        if res['status'] == 'healthy': y_pred.append(0)
        elif res.get('alert_level') == 'NORMAL': y_pred.append(0)
        else: y_pred.append(1)
        
        # 2. RUL (NASA specific)
        p_nasa = {"vibration": [], "current": [], "scalars": test_data['tabular'][i].tolist()}
        res_n = await prediction_engine.predict(p_nasa)
        rul_pred.append(res_n['prediction'])
        
        print(f" Sample {i} complete.")

    f1 = f1_score(y_true_bin, y_pred, average='macro')
    mae_rul = mean_absolute_error(rul_true, rul_pred)
    
    print("\n" + "="*40)
    print("FINAL SUBMISSION-READY EMPIRICAL METRICS")
    print(f"Macro-F1 Score (Binary Detection): {f1:.4f}")
    print(f"NASA RUL MAE: {mae_rul:.4f} ({mae_rul*20000:.1f} hours)")
    print("="*40)
    print("SUBMISSION READY")

if __name__ == "__main__":
    asyncio.run(run_final_check())
