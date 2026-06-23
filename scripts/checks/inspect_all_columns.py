import pandas as pd
import numpy as np
import os

BASE_PATH = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\Induction_Motor_Fault_Data"
LABEL_PATH = os.path.join(BASE_PATH, "lable.csv")

try:
    if os.path.exists(LABEL_PATH):
        df = pd.read_csv(LABEL_PATH, header=None)
        print("Labels loaded successfully.")
        print(f"Shape: {df.shape}")
        
        for col in df.columns:
            unique_vals = df[col].unique()
            print(f"\nColumn {col} unique values ({len(unique_vals)}):")
            if len(unique_vals) < 20:
                print(unique_vals)
            else:
                print(f"{unique_vals[:10]} ...")
                
    else:
        print("Label file not found.")

except Exception as e:
    print(f"Error: {e}")
