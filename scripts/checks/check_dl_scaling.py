import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("--- Searching for Scaling/Normalization ---")
has_scaling = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "StandardScaler" in source or "MinMaxScaler" in source or "normalize" in source.lower():
            print(f"--- Cell {i} ---")
            print(source[:500])
            has_scaling = True

if not has_scaling:
    print("\nWARNING: No scaling logic found!")
