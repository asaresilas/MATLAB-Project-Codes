import json
import os

notebook_path = 'notebooks/07_Thermal_Imaging_Training.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Update the installation cell to handle spaces in path or use %pip
# Using %pip is safer in Jupyter as it handles the current kernel automatically
new_source = [
    "# Install dependencies for the current kernel\n",
    "# Using %pip is robust against spaces in paths and environment issues\n",
    "%pip install scikit-learn matplotlib seaborn pandas tensorflow numpy\n",
    "print(\"Dependencies installed! Please restart the kernel if you still see errors.\")"
]

if nb['cells']:
    first_cell = nb['cells'][0]
    # Check if this is likely our installation cell
    if any('pip install' in line for line in first_cell['source']):
        first_cell['source'] = new_source
        print("Updated installation cell with %pip magic.")
    else:
        # Insert at top if not found (though it should be there)
        install_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": new_source
        }
        nb['cells'].insert(0, install_cell)
        print("Inserted new %pip installation cell.")

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4)

print(f"Updated {notebook_path} with robust %pip command.")
