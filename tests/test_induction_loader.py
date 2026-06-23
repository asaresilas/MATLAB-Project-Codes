import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loaders import InductionMotorLoader

def test_loader():
    data_dir = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Induction_Motor_Data/induction motor data/preprocessing/processed_data/raw'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found at {data_dir}")
        return

    print(f"Testing InductionMotorLoader with data at: {data_dir}")
    loader = InductionMotorLoader(data_dir)
    
    try:
        X, y = loader.load_all_data()
        print(f"Successfully loaded {len(X)} samples.")
        print(f"Unique labels: {np.unique(y)}")
        
        if len(X) > 0:
            print(f"Sample signal shape: {X[0].shape}")
            print("Loader Test: PASSED")
        else:
            print("Loader Test: FAILED (No data loaded)")
            
    except Exception as e:
        print(f"Loader Test: FAILED with error: {e}")

if __name__ == "__main__":
    test_loader()
