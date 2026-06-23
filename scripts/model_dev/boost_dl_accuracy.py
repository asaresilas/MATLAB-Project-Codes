"""
Increase Window Size to 60 in 02_NASA_DL_training.ipynb to boost accuracy
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "WINDOW_SIZE =" in source:
            print(f"Found Data Prep Cell at index {i}. Increasing Window Size to 60...")
            
            new_source = []
            for line in cell['source']:
                if "WINDOW_SIZE =" in line:
                    # Replace 30 (or whatever it is) with 60
                    new_source.append("WINDOW_SIZE = 60\n")
                else:
                    new_source.append(line)
            
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Increased Window Size to 60.")
else:
    print("Could not find 'WINDOW_SIZE ='.")
