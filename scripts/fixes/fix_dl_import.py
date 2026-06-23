"""
Fix import error in 03_NASA_DL_LSTM_training.ipynb
"""
import json

# Load notebook
with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the import cell
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and any('import tensorflow as pd' in line for line in cell['source']):
        # Fix the import
        new_source = []
        for line in cell['source']:
            if 'import tensorflow as pd' in line:
                new_source.append('import tensorflow as tf\n')
            else:
                new_source.append(line)
        
        cell['source'] = new_source
        print("Fixed: Replaced 'import tensorflow as pd' with 'import tensorflow as tf'")
        break

# Save
with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("✓ Notebook updated successfully.")
