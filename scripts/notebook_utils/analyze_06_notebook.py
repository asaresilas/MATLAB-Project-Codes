import json
import sys

# Load notebook
notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}\n")

# Find cells with specific keywords
keywords = ['value_counts', 'class_distribution', 'SMOTE', 'plt.legend', 'confusion_matrix', 'plt.show']

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        for keyword in keywords:
            if keyword in source:
                print(f"Cell {i} contains '{keyword}'")
                print(f"First 200 chars: {source[:200]}")
                print("-" * 80)
