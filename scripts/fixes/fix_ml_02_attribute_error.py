"""
Fix AttributeError in 02_NASA_ML_training.ipynb by keeping X as DataFrame
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "X = features_df.drop(['RUL', 'Test'], axis=1).values" in source:
            print(f"Found problematic code in Cell {i}")
            
            new_source = []
            for line in cell['source']:
                if "X = features_df.drop(['RUL', 'Test'], axis=1).values" in line:
                    # Remove .values
                    new_line = line.replace(".values", "")
                    new_source.append(new_line)
                    # Also fix y if it has .values, to be consistent (optional but good)
                elif "y = features_df['RUL'].values" in line:
                    new_line = line.replace(".values", "")
                    new_source.append(new_line)
                else:
                    new_source.append(line)
            
            cell['source'] = new_source
            fixed = True
            print("Applied fix to remove .values conversion.")

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved.")
else:
    print("Could not find the line 'X = features_df.drop...values'.")
