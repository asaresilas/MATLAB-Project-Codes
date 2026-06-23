"""
Check which column the ML notebook uses for labels and fix if needed
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CHECKING LABEL LOADING ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "labels_df" in source and "iloc" in source:
            print(f"\nCell {i}:")
            print(source[:300])

# Look for where labels are extracted
label_fixed = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        new_source = []
        for line in source:
            # Check if it's using column 2 (which has frequency values, not labels)
            if "labels_df.iloc[:, 2]" in line or "labels_df[2]" in line:
                # Replace with column 0
                new_line = line.replace("2]", "0] # Fixed: Use column 0 for labels (column 2 is frequency)")
                new_source.append(new_line)
                label_fixed = True
                print(f"Found and fixed label column in cell")
            else:
                new_source.append(line)
        cell['source'] = new_source

if label_fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("\nFixed label column (2 -> 0) in ML notebook.")
else:
    print("\nNo label column fix needed (or already using column 0).")
