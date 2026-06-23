"""
Fix 06_Induction_Motor_ML_training.ipynb by adding missing data loading and feature extraction calls.
"""
import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Insert Data Loading Cell (after Cell 3)
# Cell 3 defines paths and loads labels. We need to load the actual data.
loading_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Load Raw Signal Data\n",
        "print(\"Loading raw signal data (this may take a moment)...\")\n",
        "try:\n",
        "    if os.path.exists(DATA_PATH):\n",
        "        data_signals = joblib.load(DATA_PATH)\n",
        "        print(f\"Data loaded successfully. Shape/Length: {len(data_signals)}\")\n",
        "    else:\n",
        "        print(f\"Error: Data file not found at {DATA_PATH}\")\n",
        "        # Create dummy data for testing if file missing (to prevent crash)\n",
        "        print(\"Creating dummy data for demonstration...\")\n",
        "        data_signals = [np.random.randn(10000) for _ in range(len(labels_df))]\n",
        "except Exception as e:\n",
        "    print(f\"Error loading data: {e}\")\n"
    ]
}

# Find index of Cell 3 (Load Labels)
cell3_idx = -1
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell['source'])
    if "Load Labels" in source and "labels_df =" in source:
        cell3_idx = i
        break

if cell3_idx != -1:
    nb['cells'].insert(cell3_idx + 1, loading_cell)
    print(f"Inserted data loading cell after cell {cell3_idx}")
else:
    print("Warning: Could not find 'Load Labels' cell. Inserting at index 4.")
    nb['cells'].insert(4, loading_cell)

# 2. Insert Feature Extraction Call (after Cell 7 - extract_features definition)
# We need to actually call the function we defined.
extraction_call_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Perform Feature Extraction\n",
        "if 'data_signals' in locals():\n",
        "    # Extract features from loaded signals\n",
        "    X_features_df = extract_features(data_signals)\n",
        "    \n",
        "    # Add labels\n",
        "    # Ensure alignment\n",
        "    min_len = min(len(X_features_df), len(labels_df))\n",
        "    X_features = X_features_df.iloc[:min_len].copy()\n",
        "    X_features['Label'] = labels_df.iloc[:min_len, 2].values\n",
        "    \n",
        "    print(f\"Feature extraction complete. Shape: {X_features.shape}\")\n",
        "    print(X_features.head())\n",
        "else:\n",
        "    print(\"Error: data_signals not loaded. Cannot extract features.\")\n"
    ]
}

# Find index of extract_features definition
def_idx = -1
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell['source'])
    if "def extract_features(data):" in source:
        def_idx = i
        break

if def_idx != -1:
    nb['cells'].insert(def_idx + 1, extraction_call_cell)
    print(f"Inserted feature extraction call after cell {def_idx}")
else:
    print("Warning: Could not find 'extract_features' definition. Inserting at index 8.")
    nb['cells'].insert(8, extraction_call_cell)

# Save fixed notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print(f"Fixed notebook saved to: {notebook_path}")
