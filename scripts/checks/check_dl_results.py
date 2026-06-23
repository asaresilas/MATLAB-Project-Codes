import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("--- Searching for saving logic ---")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "save" in source.lower() or "plot" in source.lower() or "print" in source.lower():
            if "accuracy" in source.lower() or "confusion" in source.lower():
                print(f"--- Cell {i} ---")
                print(source[:500])
