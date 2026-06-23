"""
Fix TypeError in 06_Induction_Motor_DL_training.ipynb by handling one-hot encoded labels
"""
import json
import numpy as np

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the Data Balance Analysis cell
balance_idx = -1
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell.get('source', []))
    if "DATA BALANCE ANALYSIS" in source and "Counter(y_train)" in source:
        balance_idx = i
        break

if balance_idx != -1:
    print(f"Found Data Balance Analysis at cell {balance_idx}")
    cell = nb['cells'][balance_idx]
    source_lines = cell['source']
    
    # New logic to handle one-hot encoding
    new_logic = [
        "# Handle one-hot encoding (if present)\n",
        "if hasattr(y_train, 'ndim') and y_train.ndim > 1 and y_train.shape[1] > 1:\n",
        "    print(\"Detected one-hot encoded labels. Converting to indices for counting...\")\n",
        "    y_train_indices = np.argmax(y_train, axis=1)\n",
        "    y_test_indices = np.argmax(y_test, axis=1)\n",
        "else:\n",
        "    y_train_indices = y_train\n",
        "    y_test_indices = y_test\n",
        "\n",
        "# Count classes\n",
        "train_counts = Counter(y_train_indices)\n",
        "test_counts = Counter(y_test_indices)\n"
    ]
    
    # Replace the old counting logic
    new_source = []
    skip = False
    for line in source_lines:
        if "train_counts = Counter(y_train)" in line:
            new_source.extend(new_logic)
            skip = True # Skip the original lines
        elif "test_counts = Counter(y_test)" in line:
            continue # Already added in new_logic
        else:
            new_source.append(line)
            
    nb['cells'][balance_idx]['source'] = new_source
    
    # Save
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Fixed TypeError in DL notebook.")

else:
    print("Could not find Data Balance Analysis cell to fix.")
