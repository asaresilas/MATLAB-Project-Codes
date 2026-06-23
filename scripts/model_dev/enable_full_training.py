import json

notebook_path = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/notebooks/02_NASA_DL_training.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

found = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        new_source = []
        for line in cell['source']:
            if 'USE_SUBSET = True' in line:
                new_source.append(line.replace('USE_SUBSET = True', 'USE_SUBSET = False'))
                found = True
            else:
                new_source.append(line)
        cell['source'] = new_source

if found:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Successfully disabled USE_SUBSET in the notebook.")
else:
    print("Could not find 'USE_SUBSET = True' in the notebook.")
