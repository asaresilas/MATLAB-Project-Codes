"""
Fix IndexError in 06_Induction_Motor_ML_training.ipynb by updating class names
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Fix class_names in data balance analysis cell
class_names_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "class_names = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']" in line:
                new_source.append("class_names = [f'Class {i}' for i in range(7)] # Updated to match 7 unique labels in data\n")
                class_names_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if class_names_fixed:
    print("Fixed class_names in ML notebook (4 -> 7 classes).")
else:
    print("Warning: Could not find class_names to fix.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("ML notebook saved.")
