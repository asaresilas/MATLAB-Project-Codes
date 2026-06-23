"""
Dump cells 12 and 25 of 02_NASA_DL_training.ipynb
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== DUMPING CELLS ===")
for i in [12, 25, 28, 29, 30]: # Check a few relevant cells
    if i < len(nb['cells']):
        cell = nb['cells'][i]
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            print(f"\nCell {i}:")
            try:
                print(source)
            except:
                print(source.encode('ascii', 'replace').decode('ascii'))
