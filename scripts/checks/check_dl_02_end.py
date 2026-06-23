"""
Check last cells of 02_NASA_DL_training.ipynb
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
print("Last 3 cells:")
for i in range(len(nb['cells'])-3, len(nb['cells'])):
    cell = nb['cells'][i]
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        print(f"\nCell {i}:")
        try:
            print(source[:500])
        except:
            print(source.encode('ascii', 'replace').decode('ascii'))
