"""
Dump Cells 6-9 of 02_NASA_DL_training.ipynb
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== SCALING AND RESHAPING CELLS ===")
for i, cell in enumerate(nb['cells']):
    if 6 <= i <= 9:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            print(f"\nCell {i}:")
            try:
                print(source)
            except:
                print(source.encode('ascii', 'replace').decode('ascii'))
