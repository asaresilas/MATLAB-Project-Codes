import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

def fix_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # The code to insert for SMOTE
    smote_code = [
        "# Handle Class Imbalance using SMOTE\n",
        "print(\"Applying SMOTE to balance the training data...\")\n",
        "from imblearn.over_sampling import SMOTE\n",
        "\n",
        "# SMOTE works on 2D data, so we need to flatten X_train\n",
        "n_samples_train, n_time, n_channels = X_train.shape\n",
        "X_train_flat = X_train.reshape(n_samples_train, -1)\n",
        "\n",
        "# Apply SMOTE\n",
        "smote = SMOTE(random_state=42)\n",
        "X_train_resampled_flat, y_train_resampled = smote.fit_resample(X_train_flat, y_train)\n",
        "\n",
        "# Reshape back to 3D for Deep Learning models\n",
        "X_train_resampled = X_train_resampled_flat.reshape(-1, n_time, n_channels)\n",
        "\n",
        "print(f\"Original Training Shape: {X_train.shape}, {y_train.shape}\")\n",
        "print(f\"Resampled Training Shape: {X_train_resampled.shape}, {y_train_resampled.shape}\")\n",
        "\n",
        "# Update X_train and y_train to use the balanced data\n",
        "X_train = X_train_resampled\n",
        "y_train = y_train_resampled\n"
    ]

    found = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            # Identify the cell where splitting happens
            if "train_test_split" in source and "StandardScaler" in source:
                print("Found the Data Splitting cell. Injecting SMOTE...")
                
                # Split the source to insert SMOTE before StandardScaler
                split_index = -1
                for i, line in enumerate(cell['source']):
                    if "scaler = StandardScaler()" in line:
                        split_index = i
                        break
                
                if split_index != -1:
                    new_source = cell['source'][:split_index] + ["\n"] + smote_code + ["\n"] + cell['source'][split_index:]
                    cell['source'] = new_source
                    # Clear outputs to avoid confusion
                    cell['outputs'] = []
                    cell['execution_count'] = None
                    found = True
                    break
    
    if found:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Notebook updated successfully with SMOTE.")
    else:
        print("Could not find the Data Splitting cell to inject SMOTE.")

if __name__ == "__main__":
    fix_notebook()
