import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i in range(10):
    cell = nb['cells'][i]
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "x1.np" in source or "load" in source.lower():
            print(f"--- Cell {i} ---")
            print(source[:500])
