"""
Fix cell order in 06_Induction_Motor_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find indices
balance_idx = -1
split_idx = -1

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "train_test_split" in source and "y_train" in source:
             split_idx = i
        if "DATA BALANCE ANALYSIS" in source:
            balance_idx = i

if balance_idx != -1 and split_idx != -1:
    print(f"Moving Balance Cell from {balance_idx} to after {split_idx}")
    
    # Pop the balance cell
    balance_cell = nb['cells'].pop(balance_idx)
    
    # Adjust split_idx if it shifted
    if balance_idx < split_idx:
        split_idx -= 1
        
    # Insert after split cell
    nb['cells'].insert(split_idx + 1, balance_cell)
    
    # Save
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook fixed and saved.")
else:
    print("Could not find cells to reorder.")
