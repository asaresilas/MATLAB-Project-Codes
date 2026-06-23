"""
Fix NameError in 02_NASA_DL_training.ipynb by adding check for 'results' variable
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

fixed_count = 0
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "for model_name in results.keys():" in source:
            print(f"Found loop in Cell {i}")
            
            # Add check at the top
            new_source = [
                "# Check if results exist\n",
                "if 'results' not in locals():\n",
                "    print(\"⚠️ Error: 'results' not defined. Please run the Training Cell (Cell 12) first!\")\n",
                "else:\n"
            ]
            
            # Indent existing code
            for line in cell['source']:
                new_source.append("    " + line)
            
            cell['source'] = new_source
            fixed_count += 1
            print("Wrapped cell in safety check.")

if fixed_count > 0:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print(f"Notebook saved. Fixed {fixed_count} cells.")
else:
    print("No occurrences of 'for model_name in results.keys():' found.")
