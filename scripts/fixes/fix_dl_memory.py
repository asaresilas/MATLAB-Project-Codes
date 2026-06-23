"""
Fix MemoryError in 06_Induction_Motor_DL_training.ipynb by downsampling data and optimizing model
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Insert Downsampling Logic (after loading X)
# Look for: X = data_signals[:min_len]
downsample_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            new_source.append(line)
            if "X = data_signals[:min_len]" in line:
                new_source.append("\n    # FIX: Downsample data to reduce memory usage (100k -> 5k)\n")
                new_source.append("    # Taking every 20th sample preserves the signal pattern while reducing size\n")
                new_source.append("    print(f\"Original Data Shape: {np.array(X).shape}\")\n")
                new_source.append("    X = np.array([x[::20] for x in X]) # Downsample by factor of 20\n")
                new_source.append("    print(f\"Downsampled Data Shape: {X.shape}\")\n")
                downsample_fixed = True
        cell['source'] = new_source

if downsample_fixed:
    print("Added data downsampling (factor 20).")
else:
    print("Warning: Could not find data loading line to insert downsampling.")

# 2. Optimize CNN Model (Flatten -> GlobalAveragePooling1D)
# Look for: Flatten(),
model_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            if "Flatten()," in line:
                new_source.append("        # Flatten(), # Replaced with GlobalAveragePooling1D to reduce parameters\n")
                new_source.append("        tf.keras.layers.GlobalAveragePooling1D(),\n")
                model_fixed = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if model_fixed:
    print("Optimized CNN model (Flatten -> GlobalAveragePooling1D).")
else:
    print("Warning: Could not find Flatten() layer to optimize.")

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved.")
