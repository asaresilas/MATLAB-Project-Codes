"""
Fix NameError in 02_NASA_ML_training.ipynb by replacing 'results' with 'test_results'
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
            if "for model_name in results.keys():" in line:
                new_line = line.replace("results.keys()", "test_results.keys()")
                new_source_lines.append(new_line)
                fixed_count += 1
                print(f"Fixed line in Cell {i}: {line.strip()} -> {new_line.strip()}")
            elif "y_pred = results[model_name]" in line:
                new_line = line.replace("results[model_name]", "test_results[model_name]")
                new_source_lines.append(new_line)
                fixed_count += 1
                print(f"Fixed line in Cell {i}: {line.strip()} -> {new_line.strip()}")
            elif "RMSE: {results[model_name]" in line:
                new_line = line.replace("results[model_name]", "test_results[model_name]")
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
    print("No occurrences of 'results.keys()' found.")
