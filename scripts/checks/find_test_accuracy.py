"""
Dump cells containing 'test_accuracy' in 01_DL_cnn_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\01_DL_cnn_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== SEARCHING FOR 'test_accuracy' ===")
found = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "test_accuracy" in source:
            print(f"\nCell {i}:")
            print(source)
            found = True

if not found:
    print("String 'test_accuracy' NOT FOUND in any code cell.")
