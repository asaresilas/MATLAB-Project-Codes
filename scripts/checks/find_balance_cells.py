"""
Find ALL cells that have the data balance analysis code
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells in notebook: {len(nb['cells'])}\n")

# Find all cells with "DATA BALANCE ANALYSIS" or "Counter(y_train)"
print("=== CELLS WITH DATA BALANCE CODE ===\n")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'Counter(y_train)' in source or 'DATA BALANCE ANALYSIS' in source:
            print(f"Cell {i}:")
            # Show first 300 chars
            print(source[:300])
            print("\n" + "="*60 + "\n")
