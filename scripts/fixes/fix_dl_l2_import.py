"""
Fix NameError (missing l2 import) in 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "class Attention(Layer):" in source and "from tensorflow.keras.regularizers import l2" not in source:
            print(f"Found Attention Cell at index {i}. Adding l2 import...")
            
            new_source = ["from tensorflow.keras.regularizers import l2\n"] + cell['source']
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Added l2 import.")
else:
    print("Could not find Attention Cell or l2 is already imported.")
