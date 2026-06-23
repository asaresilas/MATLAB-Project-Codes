"""
Inspect 02_NASA_DL_training.ipynb to debug KeyError
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== FINDING RESULTS POPULATION ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "results =" in source or "results[" in source:
            print(f"\nCell {i}:")
            print(source[:500])
