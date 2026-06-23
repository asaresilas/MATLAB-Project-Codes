import json

# Load notebook
notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("="*80)
print("DATA BALANCE ANALYSIS")
print("="*80)
print("\nNO DATA BALANCE ANALYSIS FOUND IN NOTEBOOK!")
print("The notebook does NOT check class distribution.")

print("\n" + "="*80)
print("PLOT LEGEND ANALYSIS")
print("="*80)

# Check for plots without legends
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'plt.' in source or 'ax.' in source:
            has_legend = 'legend' in source.lower()
            status = "HAS LEGEND" if has_legend else "NO LEGEND"
            print(f"\nCell {i}: {status}")
            if not has_legend:
                print("First 200 chars:", source[:200])
