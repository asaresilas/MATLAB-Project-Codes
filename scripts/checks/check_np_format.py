
import numpy as np
import os

file_path = r"d:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Induction_Motor_Fault_Data/x1z/x1.np"

print(f"Checking file: {file_path}")
try:
    # Try loading as standard numpy file with allow_pickle=True
    data = np.load(file_path, allow_pickle=True)
    print("Loaded with np.load(allow_pickle=True)")
    print(f"Shape: {data.shape}")
    print(f"Dtype: {data.dtype}")
    
    # Check first few elements if it's an array
    if data.size > 0:
        print(f"First 5 elements: {data.flatten()[:5]}")
        
except Exception as e:
    print(f"Error: {e}")
