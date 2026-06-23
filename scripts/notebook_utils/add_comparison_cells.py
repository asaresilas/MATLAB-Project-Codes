"""
Add sequence generation and model definitions to comparison notebook
"""
import json

nb_path = 'notebooks/03_NASA_DL_Models_Comparison.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    # Cell: Sequence Generation
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Sequence Generation\n",
            "\n",
            "We use a sliding window of size **10** to create sequences for the DL models."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ============================================\n",
            "# PREPARE SEQUENCES\n",
            "# ============================================\n",
            "def create_sequences(features, targets, window_size=10):\n",
            "    X, y = [], []\n",
            "    for i in range(len(features) - window_size):\n",
            "        X.append(features[i : i + window_size])\n",
            "        y.append(targets[i + window_size])\n",
            "    return np.array(X), np.array(y)\n",
            "\n",
            "scaler = MinMaxScaler()\n",
            "feature_cols = [c for c in features_df.columns if c != 'RUL']\n",
            "X_scaled = scaler.fit_transform(features_df[feature_cols])\n",
            "y_raw = features_df['RUL'].values\n",
            "\n",
            "WINDOW_SIZE = 10\n",
            "X_seq, y_seq = create_sequences(X_scaled, y_raw, WINDOW_SIZE)\n",
            "\n",
            "# Split (60/20/20)\n",
            "train_size = int(len(X_seq) * 0.6)\n",
            "val_size = int(len(X_seq) * 0.8)\n",
            "\n",
            "X_train, y_train = X_seq[:train_size], y_seq[:train_size]\n",
            "X_val, y_val = X_seq[train_size:val_size], y_seq[train_size:val_size]\n",
            "X_test, y_test = X_seq[val_size:], y_seq[val_size:]\n",
            "\n",
            "print(f\"Train shape: {X_train.shape}\")\n",
            "print(f\"Val shape:   {X_val.shape}\")\n",
            "print(f\"Test shape:  {X_test.shape}\")"
        ]
    },
    # Cell: Model Definitions
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Define Deep Learning Models\n",
            "\n",
            "We define three architectures:\n",
            "1.  **Bi-LSTM**: Good for temporal context.\n",
            "2.  **1D-CNN**: Good for feature extraction.\n",
            "3.  **CNN-LSTM Hybrid**: Best of both."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "def build_bilstm_model(input_shape):\n",
            "    model = Sequential([\n",
            "        Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape),\n",
            "        Dropout(0.3),\n",
            "        Bidirectional(LSTM(32, return_sequences=False)),\n",
            "        Dropout(0.3),\n",
            "        Dense(1, activation='linear')\n",
            "    ])\n",
            "    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])\n",
            "    return model\n",
            "\n",
            "def build_cnn_model(input_shape):\n",
            "    model = Sequential([\n",
            "        Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),\n",
            "        MaxPooling1D(pool_size=2),\n",
            "        Conv1D(filters=32, kernel_size=3, activation='relu'),\n",
            "        Flatten(),\n",
            "        Dense(50, activation='relu'),\n",
            "        Dropout(0.3),\n",
            "        Dense(1, activation='linear')\n",
            "    ])\n",
            "    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])\n",
            "    return model\n",
            "\n",
            "def build_hybrid_model(input_shape):\n",
            "    model = Sequential([\n",
            "        Conv1D(filters=64, kernel_size=3, activation='relu', padding='same', input_shape=input_shape),\n",
            "        MaxPooling1D(pool_size=2),\n",
            "        LSTM(64, return_sequences=False),\n",
            "        Dropout(0.3),\n",
            "        Dense(1, activation='linear')\n",
            "    ])\n",
            "    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])\n",
            "    return model\n",
            "\n",
            "input_shape = (X_train.shape[1], X_train.shape[2])\n",
            "models = {\n",
            "    'Bi-LSTM': build_bilstm_model(input_shape),\n",
            "    '1D-CNN': build_cnn_model(input_shape),\n",
            "    'CNN-LSTM': build_hybrid_model(input_shape)\n",
            "}\n",
            "\n",
            "for name, model in models.items():\n",
            "    print(f\"\\n--- {name} Summary ---\")\n",
            "    model.summary()"
        ]
    },
    # Cell: Training Loop
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Train and Evaluate Models\n",
            "\n",
            "We train each model and store the results."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "results = {}\n",
            "histories = {}\n",
            "\n",
            "for name, model in models.items():\n",
            "    print(f\"\\nTraining {name}...\")\n",
            "    callbacks = [\n",
            "        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),\n",
            "        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5)\n",
            "    ]\n",
            "    \n",
            "    history = model.fit(\n",
            "        X_train, y_train,\n",
            "        validation_data=(X_val, y_val),\n",
            "        epochs=100,\n",
            "        batch_size=32,\n",
            "        callbacks=callbacks,\n",
            "        verbose=0  # Silent training to reduce clutter\n",
            "    )\n",
            "    histories[name] = history\n",
            "    \n",
            "    # Evaluate\n",
            "    y_pred = model.predict(X_test).flatten()\n",
            "    rmse = np.sqrt(mean_squared_error(y_test, y_pred))\n",
            "    mae = mean_absolute_error(y_test, y_pred)\n",
            "    r2 = r2_score(y_test, y_pred)\n",
            "    \n",
            "    results[name] = {'RMSE': rmse, 'MAE': mae, 'R2': r2, 'Predictions': y_pred}\n",
            "    print(f\"{name} Results -> RMSE: {rmse:.2f}, MAE: {mae:.2f}, R²: {r2:.4f}\")"
        ]
    }
]

nb['cells'].extend(new_cells)

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Added model definitions and training loop.")
