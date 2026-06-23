"""
Fix ValueError in 06_Induction_Motor_DL_training.ipynb by removing incorrect reshape
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Remove the problematic reshape line that forces 1 channel
# Look for: X = X.reshape(X.shape[0], X.shape[1], 1)
reshape_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "X = X.reshape(X.shape[0], X.shape[1], 1)" in line:
                # Comment it out instead of removing
                new_source.append("    # X = X.reshape(X.shape[0], X.shape[1], 1) # REMOVED: Data already has correct shape from scaling\n")
                reshape_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if reshape_fixed:
    print("Removed problematic reshape line.")
else:
    print("Warning: Could not find reshape line to remove.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
