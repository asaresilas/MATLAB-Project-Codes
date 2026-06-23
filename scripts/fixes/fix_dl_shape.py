"""
Fix ValueError in 06_Induction_Motor_DL_training.ipynb by correcting input_shape definition
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Fix input_shape definition
# Look for: input_shape = (X_train.shape[1], 1)
shape_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "input_shape = (X_train.shape[1], 1)" in line:
                # Replace with dynamic shape based on actual data dimensions
                new_source.append("input_shape = (X_train.shape[1], X_train.shape[2]) # Fixed: Use actual number of channels from data\n")
                shape_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if shape_fixed:
    print("Fixed input_shape definition to use X_train.shape[2].")
else:
    print("Warning: Could not find input_shape definition to fix.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
