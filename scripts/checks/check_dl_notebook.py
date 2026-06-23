"""
Check if 06_Induction_Motor_DL_training.ipynb needs similar fixes
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells in DL notebook: {len(nb['cells'])}")
print("\n" + "="*80)
print("CHECKING DL NOTEBOOK FOR SIMILAR ISSUES")
print("="*80)

# Check for data balance analysis
balance_keywords = ['value_counts', 'Counter', 'class_distribution', 'unique']
has_balance = False

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if any(kw in source for kw in balance_keywords):
            has_balance = True
            print(f"\nFound balance analysis in cell {i}")
            break

if not has_balance:
    print("\nNO DATA BALANCE ANALYSIS FOUND in DL notebook!")
else:
    print("\nData balance analysis EXISTS in DL notebook")

# Check for plots
print("\n" + "="*80)
print("CHECKING FOR PLOTS")
print("="*80)

plot_count = 0
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'plt.' in source or 'ax.' in source:
            plot_count += 1
            has_legend = 'legend' in source.lower()
            print(f"Cell {i}: {'HAS legend' if has_legend else 'NO legend'}")

print(f"\nTotal plotting cells: {plot_count}")
