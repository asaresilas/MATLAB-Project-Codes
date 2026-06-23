"""
Fix TypeError in 02_NASA_ML_training.ipynb by extracting RUL percentage from dictionary
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "rul = calculate_rul(file_idx, total_files_in_test)" in source:
            print(f"Found problematic code in Cell {i}")
            
            new_source = []
            for line in cell['source']:
                if "rul = calculate_rul(file_idx, total_files_in_test)" in line:
                    new_source.append("            # Fix: Extract percentage from RUL dictionary\n")
                    new_source.append("            rul_dict = calculate_rul(file_idx, total_files_in_test)\n")
                    new_source.append("            rul = rul_dict['percentage']\n")
                else:
                    new_source.append(line)
            
            cell['source'] = new_source
            fixed = True
            print("Applied fix to extract RUL percentage.")

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved.")
else:
    print("Could not find the line 'rul = calculate_rul(file_idx, total_files_in_test)'.")
