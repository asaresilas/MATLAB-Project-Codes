"""
Comprehensive fix for ML notebook - ensure correct label column and class names
"""
import json
import pandas as pd
import numpy as np
import os

# First check the actual data
BASE_PATH = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\Induction_Motor_Fault_Data"
LABEL_PATH = os.path.join(BASE_PATH, "lable.csv")

labels_df = pd.read_csv(LABEL_PATH, header=None)
print("Data inspection:")
print(f"Column 0 unique values: {np.unique(labels_df.iloc[:, 0].values)}")
print(f"Column 2 unique values: {np.unique(labels_df.iloc[:, 2].values)}")
print(f"Column 3 unique values: {np.unique(labels_df.iloc[:, 3].values)}")

# Column 0 has [0-6] which are the actual class labels
# Column 2 has [30, 35, 40, 45, 50, 55, 60] which is frequency
# Column 3 has [0, 50, 100] which is load

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"\nProcessing notebook with {len(nb['cells'])} cells...")

# Fix 1: Update label column from 2 to 0 in feature extraction cell
label_col_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "X_features['Label'] = labels_df.iloc[:min_len, 2].values" in line:
                new_source.append("    X_features['Label'] = labels_df.iloc[:min_len, 0].values # Fixed: Column 0 contains class labels (0-6)\n")
                label_col_fixed = True
                print("Fixed label column in feature extraction cell")
            else:
                new_source.append(line)
        cell['source'] = new_source

# Fix 2: Ensure class_names is correct (already done, but verify)
class_names_verified = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "class_names = [f'Class {i}' for i in range(7)]" in source:
            class_names_verified = True
            print("Verified class_names is correct (7 classes)")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("\nNotebook saved.")
print(f"Label column fixed: {label_col_fixed}")
print(f"Class names verified: {class_names_verified}")
print("\nThe notebook should now work correctly!")
