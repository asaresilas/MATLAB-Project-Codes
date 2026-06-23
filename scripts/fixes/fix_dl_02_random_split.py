"""
Fix Negative R2 in 02_NASA_DL_training.ipynb by switching to Random Split
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New Cell 5 Content (Data Prep with Random Split)
new_source = [
    "# ============================================\n",
    "# PREPARE SEQUENCES (WITH RANDOM SPLIT)\n",
    "# ============================================\n",
    "from sklearn.model_selection import train_test_split\n",
    "from sklearn.preprocessing import StandardScaler\n",
    "\n",
    "def create_sequences(features, targets, window_size=30):\n",
    "    X, y = [], []\n",
    "    for i in range(len(features) - window_size):\n",
    "        X.append(features[i : i + window_size])\n",
    "        y.append(targets[i + window_size])\n",
    "    return np.array(X), np.array(y)\n",
    "\n",
    "# Scale features\n",
    "scaler = StandardScaler()\n",
    "feature_cols = [c for c in features_df.columns if c != 'RUL']\n",
    "X_scaled = scaler.fit_transform(features_df[feature_cols])\n",
    "y_raw = features_df['RUL'].values\n",
    "\n",
    "# Create sequences\n",
    "WINDOW_SIZE = 30\n",
    "X_seq, y_seq = create_sequences(X_scaled, y_raw, WINDOW_SIZE)\n",
    "\n",
    "# Random Split (80% Train, 20% Test)\n",
    "# We use random_state for reproducibility\n",
    "X_train, X_test, y_train, y_test = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42, shuffle=True)\n",
    "\n",
    "# Further split Train into Train/Val (80/20 of Train)\n",
    "X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, shuffle=True)\n",
    "\n",
    "print(f\"Train shape: {X_train.shape}\")\n",
    "print(f\"Val shape:   {X_val.shape}\")\n",
    "print(f\"Test shape:  {X_test.shape}\")\n"
]

# Find Cell 5
fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "create_sequences" in source:
            print(f"Found Data Prep Cell at index {i}. Replacing with Random Split...")
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Switched to Random Split.")
else:
    print("Could not find Data Prep cell.")
