"""
Dump last cell of 02_NASA_DL_training.ipynb and fix 'predictions'
"""
import json
import sys

# Force utf-8 output
sys.stdout.reconfigure(encoding='utf-8')

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== LAST CELL CONTENT ===")
last_cell = nb['cells'][-1]
source = ''.join(last_cell['source'])
try:
    print(source)
except:
    print(source.encode('ascii', 'replace').decode('ascii'))

# Apply fix if needed
if "['predictions']" in source:
    print("\nFound lowercase 'predictions'. Fixing...")
    new_source = []
    for line in last_cell['source']:
        new_source.append(line.replace("['predictions']", "['Predictions']"))
    
    nb['cells'][-1]['source'] = new_source
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Fixed and saved.")
else:
    print("\nDid NOT find lowercase 'predictions'.")
