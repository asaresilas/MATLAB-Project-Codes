"""
Fix ValueError by dropping 'Test' column from X
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and update the split cell
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('X = features_df.drop' in line for line in cell['source']):
        # Update the line to drop both RUL and Test
        new_source = []
        for line in cell['source']:
            if "X = features_df.drop('RUL', axis=1).values" in line:
                new_source.append("X = features_df.drop(['RUL', 'Test'], axis=1).values  # Features (drop RUL and Test column)\n")
            else:
                new_source.append(line)
        
        cell['source'] = new_source
        print(f"Updated cell {i}: Dropped 'Test' column from X")
        break

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\n✓ Fixed ValueError: 'Test' column (string) is now excluded from training data X")
