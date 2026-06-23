"""
Inspect 01_DL_cnn_training.ipynb to debug AxisError
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\01_DL_cnn_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== MODEL DEFINITION ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "Sequential" in source or "Dense" in source:
            print(f"\nCell {i}:")
            print(source[:500])

print("\n=== PREDICTION CODE ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "model.predict" in source or "argmax" in source:
            print(f"\nCell {i}:")
            print(source[:500])
