import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

def fix_loader_header():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Fixed imports and CurrentSignatureLoader class with header handling
    imports_code = [
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "from scipy.signal import spectrogram\n",
        "from sklearn.preprocessing import LabelEncoder, StandardScaler\n",
        "from sklearn.model_selection import train_test_split\n",
        "from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, auc\n",
        "from sklearn.preprocessing import label_binarize\n",
        "from tensorflow.keras.models import Sequential\n",
        "from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, LSTM, Bidirectional\n",
        "from tensorflow.keras.utils import to_categorical\n",
        "from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau\n",
        "import os\n",
        "import glob\n",
        "\n",
        "# CurrentSignatureLoader Class Definition (FIXED HEADER)\n",
        "class CurrentSignatureLoader:\n",
        "    def __init__(self, data_dir):\n",
        "        self.data_dir = data_dir\n",
        "        self.label_map = {\n",
        "            'bearing-fault': 'bearing_fault',\n",
        "            'broken-rotor-bar': 'broken_rotor_bar',\n",
        "            'healthy': 'healthy'\n",
        "        }\n",
        "    \n",
        "    def load_raw_data(self, window_size=1000, stride=1000):\n",
        "        \"\"\"Load raw 3-phase current data from CSV files.\"\"\"\n",
        "        X_list = []\n",
        "        y_list = []\n",
        "        \n",
        "        # Check if directory exists\n",
        "        if not os.path.exists(self.data_dir):\n",
        "            print(f\"ERROR: Data directory not found: {self.data_dir}\")\n",
        "            print(f\"Current working directory: {os.getcwd()}\")\n",
        "            return np.array([]), np.array([])\n",
        "        \n",
        "        # Get all subdirectories\n",
        "        folders = [f for f in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, f))]\n",
        "        print(f\"Found {len(folders)} folders for Raw Data Loading...\")\n",
        "        \n",
        "        for folder in sorted(folders):\n",
        "            folder_path = os.path.join(self.data_dir, folder)\n",
        "            \n",
        "            # Determine label from folder name\n",
        "            label = None\n",
        "            for key, value in self.label_map.items():\n",
        "                if key in folder.lower():\n",
        "                    label = value\n",
        "                    break\n",
        "            \n",
        "            if label is None:\n",
        "                print(f\"Skipping folder (no matching label): {folder}\")\n",
        "                continue\n",
        "            \n",
        "            print(f\"Processing folder: {folder} -> Label: {label}\")\n",
        "            \n",
        "            # Load all CSV files in the folder\n",
        "            csv_files = glob.glob(os.path.join(folder_path, '*.csv'))\n",
        "            print(f\"  Found {len(csv_files)} CSV files\")\n",
        "            \n",
        "            for csv_file in csv_files:\n",
        "                try:\n",
        "                    # Read CSV with header=0 (first row is header)\n",
        "                    # The file has: Time Stamp, Current-A, Current-B, Current-C\n",
        "                    # We want columns 1, 2, 3 (Current-A, B, C)\n",
        "                    df = pd.read_csv(csv_file, header=0)\n",
        "                    \n",
        "                    # Handle different column counts\n",
        "                    if df.shape[1] < 4:\n",
        "                        print(f\"  Warning: {csv_file} has only {df.shape[1]} columns, skipping\")\n",
        "                        continue\n",
        "                    \n",
        "                    # Take columns 1, 2, 3 (skipping Time Stamp at index 0)\n",
        "                    # Ensure numeric conversion\n",
        "                    data = df.iloc[:, 1:4].apply(pd.to_numeric, errors='coerce').dropna().values\n",
        "                    \n",
        "                    if len(data) < window_size:\n",
        "                         print(f\"  Warning: {csv_file} has insufficient data ({len(data)} rows), skipping\")\n",
        "                         continue\n",
        "\n",
        "                    # Create windows\n",
        "                    num_windows = 0\n",
        "                    for i in range(0, len(data) - window_size + 1, stride):\n",
        "                        window = data[i:i+window_size, :]\n",
        "                        if window.shape == (window_size, 3):  # Ensure correct shape\n",
        "                            X_list.append(window)\n",
        "                            y_list.append(label)\n",
        "                            num_windows += 1\n",
        "                    \n",
        "                    print(f\"  Loaded {num_windows} windows from {os.path.basename(csv_file)}\")\n",
        "                    \n",
        "                except Exception as e:\n",
        "                    print(f\"  Error loading {csv_file}: {e}\")\n",
        "                    continue\n",
        "        \n",
        "        X = np.array(X_list) if X_list else np.array([])\n",
        "        y = np.array(y_list) if y_list else np.array([])\n",
        "        \n",
        "        print(f\"Raw Data Loaded: X shape={X.shape}, y shape={y.shape}\")\n",
        "        return X, y\n",
        "\n",
        "print(\"Imports and CurrentSignatureLoader loaded successfully!\")\n"
    ]

    # Find the imports cell (should be cell index 1)
    found = False
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            # Look for the imports cell (contains CurrentSignatureLoader)
            if "CurrentSignatureLoader" in source or "import numpy" in source:
                print(f"Found the imports cell at index {i}. Updating with fixed loader (header handling)...")
                cell['source'] = imports_code
                cell['outputs'] = []
                cell['execution_count'] = None
                found = True
                break
    
    if found:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Notebook updated successfully with fixed CurrentSignatureLoader (header handling).")
    else:
        print("Could not find the imports cell.")

if __name__ == "__main__":
    fix_loader_header()
