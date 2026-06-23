"""
Upgrade NASA DL Notebook to Bi-LSTM and add Advanced Features
"""
import json

# Load notebook
nb_path = 'notebooks/03_NASA_DL_LSTM_training.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Update Imports (Add Bidirectional)
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'from tensorflow.keras.layers import LSTM' in "".join(cell['source']):
        new_source = []
        for line in cell['source']:
            if 'from tensorflow.keras.layers import LSTM' in line:
                new_source.append('from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional\n')
            else:
                new_source.append(line)
        cell['source'] = new_source
        print("Updated imports.")
        break

# 2. Update Model Architecture to Bi-LSTM
bi_lstm_code = [
    "# ============================================\n",
    "# BUILD ADVANCED BI-LSTM MODEL\n",
    "# ============================================\n",
    "\n",
    "def build_lstm_model(input_shape):\n",
    "    model = Sequential([\n",
    "        # Bidirectional LSTM Layer 1\n",
    "        # Bidirectional allows the model to learn from past AND future context in the sequence\n",
    "        Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape),\n",
    "        Dropout(0.3),  # Increased dropout for regularization\n",
    "        \n",
    "        # Bidirectional LSTM Layer 2\n",
    "        Bidirectional(LSTM(32, return_sequences=False)),\n",
    "        Dropout(0.3),\n",
    "        \n",
    "        # Output Layer\n",
    "        Dense(1, activation='linear')\n",
    "    ])\n",
    "    \n",
    "    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])\n",
    "    return model\n",
    "\n",
    "input_shape = (X_train.shape[1], X_train.shape[2])\n",
    "model = build_lstm_model(input_shape)\n",
    "\n",
    "model.summary()\n"
]

for cell in nb['cells']:
    if cell['cell_type'] == 'code' and 'def build_lstm_model' in "".join(cell['source']):
        cell['source'] = bi_lstm_code
        print("Updated model architecture to Bi-LSTM.")
        break

# 3. Update Evaluation to be Comprehensive
eval_code = [
    "# ============================================\n",
    "# COMPREHENSIVE EVALUATION\n",
    "# ============================================\n",
    "\n",
    "print(\"\\n--- Detailed Performance Report ---\")\n",
    "metrics_data = []\n",
    "\n",
    "for name, X, y in [('Train', X_train, y_train), ('Val', X_val, y_val), ('Test', X_test, y_test)]:\n",
    "    pred = model.predict(X, verbose=0).flatten()\n",
    "    rmse = np.sqrt(mean_squared_error(y, pred))\n",
    "    mae = mean_absolute_error(y, pred)\n",
    "    r2 = r2_score(y, pred)\n",
    "    metrics_data.append({'Set': name, 'RMSE': rmse, 'MAE': mae, 'R2': r2})\n",
    "    print(f\"{name:5} | RMSE: {rmse:6.2f} | MAE: {mae:6.2f} | R²: {r2:6.4f}\")\n",
    "\n",
    "# Visualization: Actual vs Predicted (Test Set)\n",
    "y_pred_test = model.predict(X_test, verbose=0).flatten()\n",
    "\n",
    "plt.figure(figsize=(16, 6))\n",
    "plt.plot(y_test, label='Actual RUL', color='black', linewidth=2, alpha=0.7)\n",
    "plt.plot(y_pred_test, label='Predicted RUL (Bi-LSTM)', color='dodgerblue', linewidth=2)\n",
    "plt.title(f'Bi-LSTM RUL Prediction (Test Set)', fontsize=14)\n",
    "plt.xlabel('Time Steps (Test Set)')\n",
    "plt.ylabel('RUL (%)')\n",
    "plt.legend()\n",
    "plt.grid(True, alpha=0.3)\n",
    "plt.show()\n"
]

# Find the evaluation cell (last code cell usually)
for i in range(len(nb['cells']) - 1, -1, -1):
    cell = nb['cells'][i]
    if cell['cell_type'] == 'code' and 'model.predict' in "".join(cell['source']):
        cell['source'] = eval_code
        print("Updated evaluation section.")
        break

# 4. Add Saving Cell
save_cell_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 6. Save Model and Artifacts\n",
        "\n",
        "We save the model, scaler, and metadata for use in the application.\n"
    ]
}

save_cell_code = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ============================================\n",
        "# SAVE MODEL & ARTIFACTS\n",
        "# ============================================\n",
        "import joblib\n",
        "import json\n",
        "from datetime import datetime\n",
        "\n",
        "# Create models directory if not exists\n",
        "if not os.path.exists('../models'):\n",
        "    os.makedirs('../models')\n",
        "\n",
        "# 1. Save Keras Model\n",
        "model_path = '../models/nasa_lstm_model.keras'\n",
        "model.save(model_path)\n",
        "print(f\"Saved model to {model_path}\")\n",
        "\n",
        "# 2. Save Scaler (Crucial for inference!)\n",
        "scaler_path = '../models/nasa_scaler.pkl'\n",
        "joblib.dump(scaler, scaler_path)\n",
        "print(f\"Saved scaler to {scaler_path}\")\n",
        "\n",
        "# 3. Save Metadata\n",
        "metadata = {\n",
        "    'window_size': WINDOW_SIZE,\n",
        "    'feature_cols': list(feature_cols),\n",
        "    'training_date': datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\"),\n",
        "    'metrics': metrics_data\n",
        "}\n",
        "metadata_path = '../models/nasa_model_metadata.json'\n",
        "with open(metadata_path, 'w') as f:\n",
        "    json.dump(metadata, f, indent=4)\n",
        "print(f\"Saved metadata to {metadata_path}\")\n"
    ]
}

nb['cells'].append(save_cell_md)
nb['cells'].append(save_cell_code)
print("Added saving section.")

# Save notebook
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("✓ Notebook upgraded successfully.")
