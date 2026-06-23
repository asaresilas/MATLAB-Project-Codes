"""
Fix Overfitting in 02_NASA_DL_training.ipynb (Regularization & Simpler Models)
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New Cell 10 Content
new_source = [
    "from tensorflow.keras.regularizers import l2\n",
    "\n",
    "def build_bilstm_model(input_shape):\n",
    "    model = Sequential([\n",
    "        Bidirectional(LSTM(32, return_sequences=True, kernel_regularizer=l2(0.01)), input_shape=input_shape),\n",
    "        Dropout(0.5),\n",
    "        Bidirectional(LSTM(16, return_sequences=False, kernel_regularizer=l2(0.01))),\n",
    "        Dropout(0.5),\n",
    "        Dense(1, activation='linear')\n",
    "    ])\n",
    "    model.compile(optimizer=Adam(0.0005), loss='mse', metrics=['mae'])\n",
    "    return model\n",
    "\n",
    "def build_cnn_model(input_shape):\n",
    "    model = Sequential([\n",
    "        Conv1D(filters=32, kernel_size=3, activation='relu', kernel_regularizer=l2(0.01), input_shape=input_shape),\n",
    "        MaxPooling1D(pool_size=2),\n",
    "        Conv1D(filters=16, kernel_size=3, activation='relu', kernel_regularizer=l2(0.01)),\n",
    "        Flatten(),\n",
    "        Dense(32, activation='relu', kernel_regularizer=l2(0.01)),\n",
    "        Dropout(0.5),\n",
    "        Dense(1, activation='linear')\n",
    "    ])\n",
    "    model.compile(optimizer=Adam(0.0005), loss='mse', metrics=['mae'])\n",
    "    return model\n",
    "\n",
    "def build_hybrid_model(input_shape):\n",
    "    model = Sequential([\n",
    "        Conv1D(filters=32, kernel_size=3, activation='relu', padding='same', kernel_regularizer=l2(0.01), input_shape=input_shape),\n",
    "        MaxPooling1D(pool_size=2),\n",
    "        LSTM(32, return_sequences=False, kernel_regularizer=l2(0.01)),\n",
    "        Dropout(0.5),\n",
    "        Dense(1, activation='linear')\n",
    "    ])\n",
    "    model.compile(optimizer=Adam(0.0005), loss='mse', metrics=['mae'])\n",
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
    "    model.summary()\n"
]

# Find the cell starting with "def build_bilstm_model"
fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def build_bilstm_model" in source:
            print(f"Found Model Definition Cell at index {i}. Replacing...")
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Models updated with regularization.")
else:
    print("Could not find model definition cell.")
