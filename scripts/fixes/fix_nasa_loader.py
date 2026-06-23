"""
Fix NASALoader method name in the notebook
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Replace all instances of loader.load_file with loader.load_snapshot
changes_made = 0
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        for i, line in enumerate(cell['source']):
            if 'loader.load_file' in line:
                cell['source'][i] = line.replace('loader.load_file', 'loader.load_snapshot')
                changes_made += 1
                print(f"Fixed: {line.strip()}")

# Save updated notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print(f"\n✓ Fixed {changes_made} occurrences of 'loader.load_file' → 'loader.load_snapshot'")
