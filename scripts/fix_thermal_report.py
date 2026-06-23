import json
import os

notebook_path = 'notebooks/07_Thermal_Imaging_Training.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the evaluation cell and fix classification_report
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        modified = False
        new_source = []
        for line in source:
            if 'classification_report(y_true, y_pred, target_names=class_names)' in line:
                new_line = line.replace(
                    'classification_report(y_true, y_pred, target_names=class_names)',
                    'classification_report(y_true, y_pred, target_names=class_names, labels=range(len(class_names)), zero_division=0)'
                )
                new_source.append(new_line)
                modified = True
            else:
                new_source.append(line)
        
        if modified:
            cell['source'] = new_source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4)

print(f"Updated {notebook_path} with robust classification report.")
