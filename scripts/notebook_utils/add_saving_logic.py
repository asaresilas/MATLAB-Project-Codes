"""
Add saving logic to the DL comparison notebook.
"""
import json
import os

nb_path = 'notebooks/03_NASA_DL_training.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Save Models and Artifacts\n",
            "\n",
            "We save the trained models, scalers, and metrics to the `models` directory for future use."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
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
            "    # Create specific folder for this model type (e.g., models/dl_comparison/Bi-LSTM)\n",
            "    model_dir = os.path.join(MODELS_DIR, name.replace(' ', '_'))\n",
            "    os.makedirs(model_dir, exist_ok=True)\n",
            "    \n",
            "    # 1. Save Keras Model\n",
            "    model_path = os.path.join(model_dir, 'model.keras')\n",
            "    model.save(model_path)\n",
            "    \n",
            "    # 2. Save Scaler\n",
            "    scaler_path = os.path.join(model_dir, 'scaler.pkl')\n",
            "    joblib.dump(scaler, scaler_path)\n",
            "    \n",
            "    # 3. Save Metadata (Metrics & Config)\n",
            "    metadata = {\n",
            "        'model_name': name,\n",
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
            "    metadata_path = os.path.join(model_dir, 'metadata.json')\n",
            "    with open(metadata_path, 'w') as f:\n",
            "        json.dump(metadata, f, indent=4)\n",
            "        \n",
            "    print(f\"  ✓ Saved {name} artifacts to {model_dir}\")"
        ]
    }
]

nb['cells'].extend(new_cells)

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Added saving logic to notebook.")
