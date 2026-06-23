"""
Debug the ML notebook to understand the actual label values
"""
import json
import pandas as pd
import numpy as np
import os

# First, check what's in the notebook
notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CHECKING NOTEBOOK ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "class_names =" in source and "Class" in source:
            print(f"Cell {i} has class_names definition:")
            print(source[:200])

# Now check the actual data
print("\n=== CHECKING ACTUAL DATA ===")
BASE_PATH = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\Induction_Motor_Fault_Data"
LABEL_PATH = os.path.join(BASE_PATH, "lable.csv")

if os.path.exists(LABEL_PATH):
    labels_df = pd.read_csv(LABEL_PATH, header=None)
    
    # Check all columns
    print("\nColumn 0 unique values:", np.unique(labels_df.iloc[:, 0].values))
    print("Column 1 unique values (first 10):", np.unique(labels_df.iloc[:, 1].values)[:10])
    print("Column 2 unique values:", np.unique(labels_df.iloc[:, 2].values))
    print("Column 3 unique values:", np.unique(labels_df.iloc[:, 3].values))
    
    # The ML notebook likely uses column 2 (like the original DL notebook did)
    # But we need to check which column it's actually using
