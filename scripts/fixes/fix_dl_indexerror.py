"""
Fix IndexError in 06_Induction_Motor_DL_training.ipynb by correcting label column and class names
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Fix Label Column Index (Column 2 -> Column 0)
# Look for: y = labels_df.iloc[:min_len, 2].values
label_col_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "y = labels_df.iloc[:min_len, 2].values" in line:
                new_line = line.replace("2", "0") + " # Fixed: Changed col 2 to 0 based on data inspection\n"
                new_source.append(new_line)
                label_col_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if label_col_fixed:
    print("Fixed label column index (2 -> 0).")
else:
    print("Warning: Could not find label column loading line to fix.")

# 2. Fix Class Names (4 classes -> 7 classes)
# Look for: class_names = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']
class_names_fixed = False
new_class_names = "class_names = [f'Class {i}' for i in range(7)] # Updated to match 7 unique labels in data\n"

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "class_names =" in line and "'Healthy'" in line:
                new_source.append(new_class_names)
                class_names_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if class_names_fixed:
    print("Fixed class_names list (4 -> 7 classes).")
else:
    print("Warning: Could not find class_names definition to fix.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
