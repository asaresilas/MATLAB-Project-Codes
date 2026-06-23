import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")

split_idx = -1
balance_idx = -1

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "train_test_split" in source and "y_train =" in source: # approximate check
             split_idx = i
             print(f"Cell {i}: Defines y_train (train_test_split)")
        elif "train_test_split" in source and "y_train" in source: # broader check if above fails
             if split_idx == -1: # only if not found yet
                 split_idx = i
                 print(f"Cell {i}: Likely defines y_train (train_test_split)")
        
        if "DATA BALANCE ANALYSIS" in source:
            balance_idx = i
            print(f"Cell {i}: Data Balance Analysis")

print(f"\nSplit Cell Index: {split_idx}")
print(f"Balance Cell Index: {balance_idx}")

if balance_idx < split_idx:
    print("\nISSUE CONFIRMED: Balance analysis is BEFORE y_train definition.")
else:
    print("\nOrder seems correct? Checking content of split cell to be sure.")
    if split_idx != -1:
        print(nb['cells'][split_idx]['source'])
