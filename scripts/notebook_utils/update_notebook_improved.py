import json
import os

notebook_path = r'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\04_CIA1_DL_training.ipynb'
script_path = r'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\04_CIA1_improved_training.py'

def update_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return

    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
            
        # Create a new code cell
        new_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": script_content.splitlines(keepends=True)
        }
        
        # Add a markdown cell before it
        markdown_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Improved Training Pipeline\n",
                "\n",
                "This section implements a corrected training pipeline to address data leakage and class imbalance.\n",
                "It splits the data into Train/Validation/Test sets *before* applying SMOTE, ensuring the validation set remains pure.\n",
                "It also saves the best performing model for each architecture."
            ]
        }
        
        notebook['cells'].append(markdown_cell)
        notebook['cells'].append(new_cell)
        
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1)
            
        print(f"Successfully appended improved training code to {notebook_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_notebook()
