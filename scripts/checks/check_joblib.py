
import joblib
import sys
import numpy as np

file_path = r"d:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Induction_Motor_Fault_Data/x1z/x1.np"

print(f"Loading with joblib: {file_path}")
try:
    data = joblib.load(file_path)
    print(f"Type: {type(data)}")
    
    if hasattr(data, 'shape'):
        print(f"Shape: {data.shape}")
        print(f"Dtype: {data.dtype}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
    elif isinstance(data, dict):
        print(f"Dict keys: {list(data.keys())[:10]}")
            
except Exception as e:
    print(f"Error: {e}")
