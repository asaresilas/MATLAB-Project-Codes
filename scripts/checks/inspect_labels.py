import json
import joblib
import pandas as pd
import numpy as np
import os

# Define paths (mimicking the notebook)
BASE_PATH = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\Induction_Motor_Fault_Data"
LABEL_PATH = os.path.join(BASE_PATH, "lable.csv")
DATA_PATH = os.path.join(BASE_PATH, "x1z", "x1.np")

print(f"Checking labels from: {LABEL_PATH}")

try:
    # Load Labels
    if os.path.exists(LABEL_PATH):
        labels_df = pd.read_csv(LABEL_PATH, header=None)
        print("Labels loaded successfully.")
        
        # Inspect the label column (assuming index 2 based on previous notebook code)
        # "y = labels_df.iloc[:min_len, 2].values"
        y_raw = labels_df.iloc[:, 2].values
        unique_labels = np.unique(y_raw)
        
        print(f"Unique labels found in CSV column 2: {unique_labels}")
        print(f"Number of unique labels: {len(unique_labels)}")
        
        # Check if there are other columns that might be labels
        print("\nFirst 5 rows of dataframe:")
        print(labels_df.head())
        
    else:
        print("Label file not found.")

except Exception as e:
    print(f"Error: {e}")
