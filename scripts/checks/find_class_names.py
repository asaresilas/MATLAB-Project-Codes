"""
Check the exact content of the data balance analysis cell in ML notebook
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The error says Cell In[9], so let's find all cells with class_names
print("=== ALL CELLS WITH 'class_names' ===\n")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'class_names' in source:
            print(f"Cell {i}:")
            print(source)
            print("\n" + "="*60 + "\n")
