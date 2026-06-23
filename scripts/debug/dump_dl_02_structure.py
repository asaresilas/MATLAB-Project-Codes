"""
Dump notebook structure of 02_NASA_DL_training.ipynb
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, cell in enumerate(nb['cells']):
    cell_type = cell['cell_type']
    source = cell['source']
    first_line = source[0].strip() if source else "<empty>"
    print(f"Cell {i} ({cell_type}): {first_line[:50]}")
