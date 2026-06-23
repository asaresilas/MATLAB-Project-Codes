import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

def fix_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # The new correct code block
    new_code = [
        "# Encode Labels\n",
        "le = LabelEncoder()\n",
        "y_enc = le.fit_transform(y)\n",
        "class_names = le.classes_\n",
        "print(f\"Classes: {class_names}\")\n",
        "\n",
        "# Split Data (Use y_enc for labels to support SMOTE)\n",
        "X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)\n",
        "\n",
        "# --- Data Augmentation ---\n",
        "def add_noise(data, noise_level=0.005):\n",
        "    noise = np.random.normal(0, noise_level, data.shape)\n",
        "    return data + noise\n",
        "\n",
        "def time_shift(data, shift_max=50):\n",
        "    shift = np.random.randint(-shift_max, shift_max)\n",
        "    return np.roll(data, shift, axis=1)\n",
        "\n",
        "print(\"Augmenting Training Data...\")\n",
        "X_train_noise = add_noise(X_train)\n",
        "X_train_shift = np.array([time_shift(x) for x in X_train])\n",
        "\n",
        "# Combine\n",
        "X_train = np.concatenate((X_train, X_train_noise, X_train_shift), axis=0)\n",
        "y_train = np.concatenate((y_train, y_train, y_train), axis=0)\n",
        "print(f\"Augmented Train Shape: {X_train.shape}\")\n",
        "\n",
        "# Handle NaNs (Fix for ValueError)\n",
        "if np.isnan(X_train).any():\n",
        "    print(\"NaNs found in training data. Imputing with 0...\")\n",
        "    X_train = np.nan_to_num(X_train, nan=0.0)\n",
        "\n",
        "# Handle Class Imbalance using SMOTE\n",
        "print(\"Applying SMOTE to balance the training data...\")\n",
        "from imblearn.over_sampling import SMOTE\n",
        "\n",
        "# SMOTE works on 2D data (Samples, Features)\n",
        "n_samples, n_time, n_channels = X_train.shape\n",
        "X_train_flat = X_train.reshape(n_samples, -1)\n",
        "\n",
        "# Apply SMOTE\n",
        "smote = SMOTE(random_state=42)\n",
        "X_train_resampled_flat, y_train_resampled = smote.fit_resample(X_train_flat, y_train)\n",
        "\n",
        "# Reshape back to 3D\n",
        "X_train = X_train_resampled_flat.reshape(-1, n_time, n_channels)\n",
        "y_train_labels = y_train_resampled\n",
        "\n",
        "print(f\"Resampled Training Shape: {X_train.shape}, {y_train_labels.shape}\")\n",
        "\n",
        "# Convert to Categorical for Deep Learning\n",
        "y_train = to_categorical(y_train_labels)\n",
        "y_test = to_categorical(y_test)\n",
        "\n",
        "# Scale Data (StandardScaler per channel)\n",
        "# Reshape to (Samples*Time, Channels)\n",
        "X_train_flat_scale = X_train.reshape(-1, n_channels)\n",
        "X_test_flat_scale = X_test.reshape(-1, n_channels)\n",
        "\n",
        "# Handle NaNs in Test Data if any\n",
        "if np.isnan(X_test_flat_scale).any():\n",
        "     X_test_flat_scale = np.nan_to_num(X_test_flat_scale, nan=0.0)\n",
        "\n",
        "scaler = StandardScaler()\n",
        "X_train_scaled_flat = scaler.fit_transform(X_train_flat_scale)\n",
        "X_test_scaled_flat = scaler.transform(X_test_flat_scale)\n",
        "\n",
        "# Reshape back to (Samples, Time, Channels)\n",
        "X_train_scaled = X_train_scaled_flat.reshape(-1, n_time, n_channels)\n",
        "X_test_scaled = X_test_scaled_flat.reshape(-1, n_time, n_channels)\n",
        "\n",
        "print(f\"Train Scaled Shape: {X_train_scaled.shape}\")\n",
        "print(f\"Test Scaled Shape: {X_test_scaled.shape}\")\n"
    ]

    found = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            # Identify the cell where splitting happens
            if "# Encode Labels" in source:
                print("Found the Data Splitting/Preprocessing cell. Replacing content...")
                cell['source'] = new_code
                cell['outputs'] = []
                cell['execution_count'] = None
                found = True
                break
    
    if found:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Notebook updated successfully with fixed SMOTE and NaN handling logic.")
    else:
        print("Could not find the Data Splitting cell to update.")

if __name__ == "__main__":
    fix_notebook()
