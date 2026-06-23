"""
Inspect 02_NASA_ML_training.ipynb to debug NameError
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CHECKING PATH DEFINITIONS ===")
for i, cell in enumerate(nb['cells']):
    if i > 5: break # Only check first 5 cells
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        print(f"\nCell {i}:")
        print(source)
