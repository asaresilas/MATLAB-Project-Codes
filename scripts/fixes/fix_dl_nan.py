"""
Fix ValueError in 06_Induction_Motor_DL_training.ipynb by handling NaN/Infinity values
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Insert Data Cleaning Logic (before scaling)
# Look for: scaler = StandardScaler()
cleaning_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "scaler = StandardScaler()" in line:
                # Insert cleaning BEFORE scaling
                new_source.append("\n    # FIX: Handle NaN and Infinity values before scaling\n")
                new_source.append("    print(\"Checking for NaN or Infinity values...\")\n")
                new_source.append("    # Check if X_flat is a DataFrame or numpy array\n")
                new_source.append("    if hasattr(X_flat, 'replace'): # DataFrame\n")
                new_source.append("        X_flat.replace([np.inf, -np.inf], np.nan, inplace=True)\n")
                new_source.append("        X_flat.fillna(X_flat.mean(), inplace=True)\n")
                new_source.append("    else: # Numpy array\n")
                new_source.append("        X_flat = np.nan_to_num(X_flat, nan=0.0, posinf=0.0, neginf=0.0)\n")
                new_source.append("    print(\"Data cleaned (NaN/Inf removed).\")\n")
                new_source.append("    \n")
                
                new_source.append(line) # The original scaler line
                cleaning_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if cleaning_fixed:
    print("Added NaN/Infinity handling logic.")
else:
    print("Warning: Could not find StandardScaler line to insert cleaning.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
