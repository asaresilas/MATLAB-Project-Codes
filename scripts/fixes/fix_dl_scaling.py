"""
Fix 06_Induction_Motor_DL_training.ipynb by adding StandardScaler
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Insert Scaling Logic (after reshaping X)
# Look for: X = X.reshape(X.shape[0], X.shape[1], 1)
# Note: We need to scale BEFORE reshaping to 3D, or reshape back and forth.
# Easier: Scale 2D (samples, features) then reshape.

scaling_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "X = X.reshape" in line:
                # Insert scaling BEFORE reshaping
                new_source.append("\n    # FIX: Scale data for better convergence\n")
                new_source.append("    print(\"Scaling data...\")\n")
                new_source.append("    # Reshape to 2D for scaling: (samples, time_steps * channels)\n")
                new_source.append("    # But wait, X is currently (samples, time_steps, channels) or (samples, time_steps)\n")
                new_source.append("    # Let's handle the scaling carefully.\n")
                new_source.append("    \n")
                new_source.append("    # 1. Flatten for scaling\n")
                new_source.append("    orig_shape = X.shape\n")
                new_source.append("    if X.ndim == 3:\n")
                new_source.append("        X_flat = X.reshape(orig_shape[0], -1)\n")
                new_source.append("    else:\n")
                new_source.append("        X_flat = X\n")
                new_source.append("        \n")
                new_source.append("    # 2. Scale\n")
                new_source.append("    scaler = StandardScaler()\n")
                new_source.append("    X_scaled = scaler.fit_transform(X_flat)\n")
                new_source.append("    \n")
                new_source.append("    # 3. Reshape back\n")
                new_source.append("    if len(orig_shape) == 3:\n")
                new_source.append("        X = X_scaled.reshape(orig_shape)\n")
                new_source.append("    else:\n")
                new_source.append("        X = X_scaled\n")
                new_source.append("    \n")
                new_source.append("    print(\"Data scaled.\")\n")
                new_source.append("    \n")
                
                new_source.append(line) # The original reshape line
                scaling_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if scaling_fixed:
    print("Added StandardScaler logic.")
else:
    print("Warning: Could not find reshape line to insert scaling.")
    # Fallback: Try to find "New Data Shape" print
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            new_source = []
            for line in source:
                if "New Data Shape:" in line:
                     # Insert BEFORE this print
                    new_source.append("\n    # FIX: Scale data (Fallback insertion)\n")
                    new_source.append("    scaler = StandardScaler()\n")
                    new_source.append("    # Reshape to 2D, scale, reshape back\n")
                    new_source.append("    orig_shape = X.shape\n")
                    new_source.append("    X = scaler.fit_transform(X.reshape(orig_shape[0], -1)).reshape(orig_shape)\n")
                    new_source.append("    print(\"Data scaled.\")\n")
                    new_source.append(line)
                    scaling_fixed = True
                else:
                    new_source.append(line)
            cell['source'] = new_source
            if scaling_fixed: break

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
