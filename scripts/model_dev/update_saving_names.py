"""
Update saving logic to use descriptive filenames.
"""
import json
import os

nb_path = 'notebooks/03_NASA_DL_training.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The saving cell is the last one
saving_cell = nb['cells'][-1]

# New source code with descriptive filenames
new_source = [
    "import joblib\n",
    "import json\n",
    "from datetime import datetime\n",
    "\n",
    "# Create base models directory if it doesn't exist\n",
    "MODELS_DIR = os.path.abspath(os.path.join('..', 'models', 'dl_comparison'))\n",
    "os.makedirs(MODELS_DIR, exist_ok=True)\n",
    "\n",
    "print(f\"Saving models to: {MODELS_DIR}\")\n",
    "\n",
    "for name, model in models.items():\n",
    "    # Clean name for filesystem (e.g., 'Bi-LSTM' -> 'Bi-LSTM')\n",
    "    clean_name = name.replace(' ', '_')\n",
    "    \n",
    "    # Create specific folder for this model type\n",
    "    model_dir = os.path.join(MODELS_DIR, clean_name)\n",
    "    os.makedirs(model_dir, exist_ok=True)\n",
    "    \n",
    "    # 1. Save Keras Model with Descriptive Name\n",
    "    # e.g., Bi-LSTM_model.keras\n",
    "    model_filename = f\"{clean_name}_model.keras\"\n",
    "    model_path = os.path.join(model_dir, model_filename)\n",
    "    model.save(model_path)\n",
    "    \n",
    "    # 2. Save Scaler with Descriptive Name\n",
    "    # e.g., Bi-LSTM_scaler.pkl\n",
    "    scaler_filename = f\"{clean_name}_scaler.pkl\"\n",
    "    scaler_path = os.path.join(model_dir, scaler_filename)\n",
    "    joblib.dump(scaler, scaler_path)\n",
    "    \n",
    "    # 3. Save Metadata (Metrics & Config)\n",
    "    metadata = {\n",
    "        'model_name': name,\n",
    "        'filename': model_filename,\n",
    "        'scaler_filename': scaler_filename,\n",
    "        'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),\n",
    "        'metrics': {\n",
    "            'RMSE': float(results[name]['RMSE']),\n",
    "            'MAE': float(results[name]['MAE']),\n",
    "            'R2': float(results[name]['R2'])\n",
    "        },\n",
    "        'input_shape': input_shape,\n",
    "        'window_size': WINDOW_SIZE\n",
    "    }\n",
    "    \n",
    "    metadata_path = os.path.join(model_dir, f\"{clean_name}_metadata.json\")\n",
    "    with open(metadata_path, 'w') as f:\n",
    "        json.dump(metadata, f, indent=4)\n",
    "        \n",
    "    print(f\"  ✓ Saved {name} artifacts to {model_dir}\")\n",
    "    print(f\"    - Model: {model_filename}\")\n",
    "    print(f\"    - Scaler: {scaler_filename}\")"
]

saving_cell['source'] = new_source

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Updated saving logic with descriptive filenames.")
