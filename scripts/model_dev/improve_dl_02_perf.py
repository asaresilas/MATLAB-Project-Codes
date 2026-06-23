"""
Improve performance in 02_NASA_DL_training.ipynb (Window Size 30, StandardScaler)
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "WINDOW_SIZE = 10" in source:
            print(f"Found Cell {i} (Data Prep). Applying improvements...")
            
            new_source = []
            for line in cell['source']:
                # Increase Window Size
                if "WINDOW_SIZE = 10" in line:
                    new_source.append(line.replace("10", "30"))
                # Switch to StandardScaler
                elif "MinMaxScaler" in line:
                    new_source.append(line.replace("MinMaxScaler", "StandardScaler"))
                else:
                    new_source.append(line)
            
            # Add import for StandardScaler if not present
            if "from sklearn.preprocessing import StandardScaler" not in ''.join(new_source):
                new_source.insert(0, "from sklearn.preprocessing import StandardScaler\n")
            
            cell['source'] = new_source
            fixed = True

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Increased Window Size and switched to StandardScaler.")
else:
    print("Could not find 'WINDOW_SIZE = 10'.")
