import json
import os

def convert_notebook_to_script(notebook_path, script_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    script_content = []
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            if isinstance(source, str):
                source = source.split('\n')
            
            for line in source:
                # Path Fixes for Root Execution
                line = line.replace("../NASA_Data", "datasets/NASA")
                line = line.replace("../datasets", "datasets")
                line = line.replace("../Trained_models", "Trained_models")
                line = line.replace("../models", "models")
                
                # Comment out sys.path.append('..') as we are in root
                if "sys.path.append" in line and ".." in line:
                    line = f"# {line}"

                if line.strip().startswith('!'):
                    script_content.append(f"# {line}")
                elif line.strip().startswith('%'):
                    script_content.append(f"# {line}")
                else:
                    script_content.append(line)
            script_content.append('\n')
            
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(''.join(script_content))
    print(f"Converted {notebook_path} to {script_path} with path fixes.")

if __name__ == "__main__":
    convert_notebook_to_script('notebooks/02_NASA_DL_training.ipynb', 'train_nasa_dl.py')
