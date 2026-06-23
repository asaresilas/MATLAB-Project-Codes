import os
import json
import glob

notebooks = glob.glob('notebooks/*.ipynb')
out = []

keywords = ['loadmat', 'read_csv', 'os.listdir', 'def load', 'Image.open', 'cv2.imread']

for nb in notebooks:
    if 'ML' in nb: continue # Skip ML notebooks since DL logic is same
    try:
        data = json.load(open(nb, 'r', encoding='utf-8'))
        cells = data.get('cells', [])
        for i, cell in enumerate(cells[:15]): # data loading is usually in first 15 cells
            if cell['cell_type'] == 'code':
                source = "".join(cell.get('source', []))
                if any(k in source for k in keywords):
                    out.append(f"------ {os.path.basename(nb)} - Cell {i} ------\n{source}\n")
    except Exception:
        pass

with open('data_loaders.txt', 'w', encoding='utf-8') as f:
    f.writelines(out)
