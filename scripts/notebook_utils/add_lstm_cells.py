"""
Add sequence generation and LSTM model cells to notebook
"""
import json

# Load notebook
with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    # Cell: Markdown - Sequence Generation
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Sequence Generation (Sliding Window)\n",
            "\n",
            "LSTM requires 3D input: `(samples, time_steps, features)`\n",
            "\n",
            "We use a **Sliding Window** approach:\n",
            "- **Window Size (Sequence Length)**: 10 (Look at past 10 files)\n",
            "- **Target**: RUL of the *last* file in the window\n",
            "\n",
            "```\n",
            "[t-9, t-8, ..., t-1, t] -> Predict RUL(t)\n",
            "```\n"
        ]
    },
    
    # Cell: Code - Sequence Generator
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ============================================\n",
            "# PREPARE SEQUENCES FOR LSTM\n",
            "# ============================================\n",
            "\n",
            "def create_sequences(features, targets, window_size=10):\n",
            "    \"\"\"\n",
            "    Convert 2D features into 3D sequences.\n",
            "    \"\"\"\n",
            "    X, y = [], []\n",
            "    for i in range(len(features) - window_size):\n",
            "        X.append(features[i : i + window_size])\n",
            "        y.append(targets[i + window_size])\n",
            "    return np.array(X), np.array(y)\n",
            "\n",
            "# 1. Scale Features (Important for LSTM!)\n",
            "# We use MinMaxScaler to scale to [0, 1] range\n",
            "scaler = MinMaxScaler()\n",
            "feature_cols = [c for c in features_df.columns if c not in ['RUL', 'Test']]\n",
            "X_scaled = scaler.fit_transform(features_df[feature_cols])\n",
            "y_raw = features_df['RUL'].values\n",
            "\n",
            "# 2. Create Sequences\n",
            "WINDOW_SIZE = 10\n",
            "X_seq, y_seq = create_sequences(X_scaled, y_raw, WINDOW_SIZE)\n",
            "\n",
            "print(f\"Original shape: {X_scaled.shape}\")\n",
            "print(f\"Sequence shape: {X_seq.shape}  (Samples, Time Steps, Features)\")\n",
            "\n",
            "# 3. Split Data (Temporal)\n",
            "train_size = int(len(X_seq) * 0.6)\n",
            "val_size = int(len(X_seq) * 0.8)\n",
            "\n",
            "X_train, y_train = X_seq[:train_size], y_seq[:train_size]\n",
            "X_val, y_val = X_seq[train_size:val_size], y_seq[train_size:val_size]\n",
            "X_test, y_test = X_seq[val_size:], y_seq[val_size:]\n",
            "\n",
            "print(f\"\\nTrain: {X_train.shape[0]} samples\")\n",
            "print(f\"Val:   {X_val.shape[0]} samples\")\n",
            "print(f\"Test:  {X_test.shape[0]} samples\")\n"
        ]
    },
    
    # Cell: Markdown - Model Architecture
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Build LSTM Model\n",
            "\n",
            "**Architecture:**\n",
            "1. **LSTM Layer 1**: 64 units, return sequences (pass to next LSTM)\n",
            "2. **Dropout**: 20% (prevent overfitting)\n",
            "3. **LSTM Layer 2**: 32 units, no return sequences (final state)\n",
            "4. **Dropout**: 20%\n",
            "5. **Dense Layer**: 1 unit (Regression output)\n"
        ]
    },
    
    # Cell: Code - Build Model
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ============================================\n",
            "# BUILD LSTM MODEL\n",
            "# ============================================\n",
            "\n",
            "def build_lstm_model(input_shape):\n",
            "    model = Sequential([\n",
            "        # First LSTM Layer\n",
            "        LSTM(64, return_sequences=True, input_shape=input_shape),\n",
            "        Dropout(0.2),\n",
            "        \n",
            "        # Second LSTM Layer\n",
            "        LSTM(32, return_sequences=False),\n",
            "        Dropout(0.2),\n",
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
    }
]

nb['cells'].extend(new_cells)

with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Added sequence generation and LSTM model cells.")
