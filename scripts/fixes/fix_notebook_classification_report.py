import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\05_Universal_Model_Training.ipynb"

if not os.path.exists(notebook_path):
    print(f"Error: Notebook not found at {notebook_path}")
    exit(1)

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    modified_count = 0
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            new_source = []
            cell_modified = False
            for line in source:
                if 'print(classification_report(true_class_idx, pred_class_idx, target_names=class_names, zero_division=0))' in line:
                    new_line = line.replace(
                        'print(classification_report(true_class_idx, pred_class_idx, target_names=class_names, zero_division=0))',
                        'print(classification_report(true_class_idx, pred_class_idx, target_names=class_names, labels=range(len(class_names)), zero_division=0))'
                    )
                    new_source.append(new_line)
                    cell_modified = True
                    modified_count += 1
                else:
                    new_source.append(line)
            
            if cell_modified:
                cell['source'] = new_source

    if modified_count > 0:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=4)
        print(f"Successfully fixed {modified_count} classification_report call(s).")
    else:
        print("No classification_report calls needing fix were found.")

except Exception as e:
    print(f"An error occurred: {e}")
