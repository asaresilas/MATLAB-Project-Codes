"""
Fix AxisError in 01_DL_cnn_training.ipynb by removing incorrect argmax usage
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\01_DL_cnn_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the cell with the error
fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "y_pred_classes = np.argmax(y_pred, axis=1)" in source:
            print(f"Found problematic code in Cell {i}")
            
            new_source = []
            for line in cell['source']:
                if "y_pred_classes = np.argmax(y_pred, axis=1)" in line:
                    # Replace with logic that checks dimensions
                    new_source.append("# Fixed AxisError: Check dimensions before argmax\n")
                    new_source.append("if y_pred.ndim > 1:\n")
                    new_source.append("    y_pred_classes = np.argmax(y_pred, axis=1)\n")
                    new_source.append("else:\n")
                    new_source.append("    y_pred_classes = y_pred\n")
                elif "y_test_classes = np.argmax(y_test, axis=1)" in line:
                    new_source.append("if y_test.ndim > 1:\n")
                    new_source.append("    y_test_classes = np.argmax(y_test, axis=1)\n")
                    new_source.append("else:\n")
                    new_source.append("    y_test_classes = y_test\n")
                else:
                    new_source.append(line)
            
            cell['source'] = new_source
            fixed = True
            print("Applied fix to handle 1D/2D arrays robustly.")

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved.")
else:
    print("Could not find the specific line to fix.")
