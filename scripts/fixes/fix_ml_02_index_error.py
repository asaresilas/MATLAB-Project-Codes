"""
Fix InvalidIndexError in 02_NASA_ML_training.ipynb by using .iloc for DataFrame indexing
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed_count = 0
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source_lines = cell['source']
        new_source_lines = []
        for line in source_lines:
            # Check for X_train[:, pattern
            if "X_train[:," in line:
                new_line = line.replace("X_train[:,", "X_train.iloc[:,")
                new_source_lines.append(new_line)
                fixed_count += 1
                print(f"Fixed line in Cell {i}: {line.strip()} -> {new_line.strip()}")
            elif "X_test[:," in line:
                new_line = line.replace("X_test[:,", "X_test.iloc[:,")
                new_source_lines.append(new_line)
                fixed_count += 1
                print(f"Fixed line in Cell {i}: {line.strip()} -> {new_line.strip()}")
            elif "X_val[:," in line:
                new_line = line.replace("X_val[:,", "X_val.iloc[:,")
                new_source_lines.append(new_line)
                fixed_count += 1
                print(f"Fixed line in Cell {i}: {line.strip()} -> {new_line.strip()}")
            else:
                new_source_lines.append(line)
        cell['source'] = new_source_lines

if fixed_count > 0:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print(f"Notebook saved. Fixed {fixed_count} occurrences.")
else:
    print("No occurrences of 'X_train[:,' found.")
