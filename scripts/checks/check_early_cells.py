import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i in range(13):
    cell = nb['cells'][i]
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        print(f"--- Cell {i} ---")
        print(source[:300])
        print("...")
        if "X_features =" in source or "X_features=" in source:
            print(">>> DEFINES X_features")
