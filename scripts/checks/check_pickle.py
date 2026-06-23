
import pickle
import sys

file_path = r"d:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Induction_Motor_Fault_Data/x1z/x1.np"

print(f"Loading pickle: {file_path}")
try:
    with open(file_path, 'rb') as f:
        # Just try to load the object structure, not print the whole thing
        data = pickle.load(f)
        print(f"Type: {type(data)}")
        
        if hasattr(data, 'shape'):
            print(f"Shape: {data.shape}")
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
            print(f"First element type: {type(data[0])}")
        elif isinstance(data, dict):
            print(f"Dict keys: {list(data.keys())[:10]}")
            
except Exception as e:
    print(f"Error: {e}")
