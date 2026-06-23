"""
Inspect 02_NASA_ML_training.ipynb to debug TypeError (y_train is dict)
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CHECKING DATA PREPARATION ===")
for i, cell in enumerate(nb['cells']):
    if 5 <= i <= 15: # Check cells around data loading
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if "X.append" in source or "y.append" in source or "train_test_split" in source:
                print(f"\nCell {i}:")
                try:
                    print(source)
                except:
                    print(source.encode('ascii', 'replace').decode('ascii'))
