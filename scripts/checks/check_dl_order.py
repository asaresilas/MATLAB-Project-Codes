import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")

split_idx = -1
balance_idx = -1

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "train_test_split" in source and "y_train" in source:
             split_idx = i
             print(f"Cell {i}: Defines y_train (train_test_split)")
        
        if "DATA BALANCE ANALYSIS" in source:
            balance_idx = i
            print(f"Cell {i}: Data Balance Analysis")

print(f"\nSplit Cell Index: {split_idx}")
print(f"Balance Cell Index: {balance_idx}")

if balance_idx != -1 and balance_idx < split_idx:
    print("\nISSUE CONFIRMED: Balance analysis is BEFORE y_train definition.")
elif balance_idx == -1:
    print("\nISSUE: Balance analysis cell NOT FOUND.")
elif split_idx == -1:
    print("\nISSUE: train_test_split cell NOT FOUND.")
else:
    print("\nOrder seems correct? Checking content of split cell.")
