import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("--- Data Loading & Reshaping ---")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "reshape" in source or "X =" in source or "X.shape" in source:
            print(f"--- Cell {i} ---")
            print(source[:500])

print("\n--- Model Definition ---")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "Sequential" in source or "Conv1D" in source:
            print(f"--- Cell {i} ---")
            print(source[:500])
