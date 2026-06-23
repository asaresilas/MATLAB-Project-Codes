import json
import sys

# Load the notebook
with open('notebooks/01_DL_cnn_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
print(f"Code cells: {sum(1 for c in nb['cells'] if c['cell_type'] == 'code')}")
print(f"Markdown cells: {sum(1 for c in nb['cells'] if c['cell_type'] == 'markdown')}")
print("\n" + "="*60)
print("CELL STRUCTURE:")
print("="*60)

for i, cell in enumerate(nb['cells']):
    cell_type = cell['cell_type']
    if cell['source']:
        first_line = cell['source'][0][:70]
    else:
        first_line = "(empty)"
    print(f"\nCell {i}: [{cell_type.upper()}]")
    print(f"  Content: {first_line}...")
