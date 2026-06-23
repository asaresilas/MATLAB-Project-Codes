"""
Inspect 02_NASA_ML_training.ipynb to debug NameError (Unicode Safe)
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CHECKING PATH DEFINITIONS ===")
for i, cell in enumerate(nb['cells']):
    if i > 5: break
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        print(f"\nCell {i}:")
        try:
            print(source)
        except Exception as e:
            print(f"Error printing source: {e}")
            print(source.encode('ascii', 'replace').decode('ascii'))
