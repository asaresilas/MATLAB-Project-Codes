import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

def debug_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    print(f"Total cells: {len(nb['cells'])}")
    
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "LabelEncoder" in source:
                print(f"Found LabelEncoder in cell {i}")
                print("Source snippet:", source[:200])
                # Attempt replace here
                print("Attempting replacement...")
                cell['source'] = ["# REPLACED BY DEBUG SCRIPT\n"]
                
                with open(notebook_path, 'w', encoding='utf-8') as f:
                    json.dump(nb, f, indent=1)
                print("File written.")
                return

    print("LabelEncoder not found in any code cell.")

if __name__ == "__main__":
    debug_notebook()
