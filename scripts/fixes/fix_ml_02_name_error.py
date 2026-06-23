"""
Fix NameError in 02_NASA_ML_training.ipynb by defining TEST_PATH and data_files in Cell 5
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "loader = NASALoader(TEST_PATH)" in source:
            print(f"Found problematic code in Cell {i}")
            
            # Add definitions at the top of the cell
            new_source = [
                "# Fix: Define TEST_PATH and data_files using 2nd_test (standard)\n",
                "TEST_PATH = test_configs['2nd_test']\n",
                "data_files = test_info['2nd_test']['files']\n",
                "\n"
            ]
            new_source.extend(cell['source'])
            
            cell['source'] = new_source
            fixed = True
            print("Applied fix to define TEST_PATH.")

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved.")
else:
    print("Could not find the cell with 'loader = NASALoader(TEST_PATH)'.")
