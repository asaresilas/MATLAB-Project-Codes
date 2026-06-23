import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("--- Cell 9 ---")
if len(nb['cells']) > 9:
    print(''.join(nb['cells'][9]['source']))
else:
    print("Cell 9 does not exist.")
