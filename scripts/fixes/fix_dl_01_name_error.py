"""
Fix NameError in 01_DL_cnn_training.ipynb by renaming test_accuracy to test_acc
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\01_DL_cnn_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "test_accuracy" in line and "test_acc" not in line:
                # Replace test_accuracy with test_acc
                new_line = line.replace("test_accuracy", "test_acc")
                new_source.append(new_line)
                fixed = True
                print(f"Fixed variable name in Cell {i}")
            else:
                new_source.append(line)
        cell['source'] = new_source

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved with variable name fix.")
else:
    print("Could not find 'test_accuracy' to fix.")
