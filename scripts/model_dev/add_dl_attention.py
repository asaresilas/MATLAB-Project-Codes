"""
Add Attention Mechanism to Bi-LSTM in 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New Cell 10 Content with Attention
new_source = [
    "from tensorflow.keras.layers import Layer\n",
    "import tensorflow.keras.backend as K\n",
    "\n",
    "class Attention(Layer):\n",
    "    def __init__(self, **kwargs):\n",
    "        super(Attention, self).__init__(**kwargs)\n",
    "    def build(self, input_shape):\n",
    "        self.W = self.add_weight(name='attention_weight', shape=(input_shape[-1], 1), initializer='normal')\n",
    "        self.b = self.add_weight(name='attention_bias', shape=(input_shape[1], 1), initializer='zeros')\n",
    "        super(Attention, self).build(input_shape)\n",
    "    def call(self, x):\n",
    "        e = K.tanh(K.dot(x, self.W) + self.b)\n",
    "        a = K.softmax(e, axis=1)\n",
    "        output = x * a\n",
    "        return K.sum(output, axis=1)\n",
    "\n",
    "def build_bilstm_model(input_shape):\n",
    "    # Bi-LSTM with Attention\n",
    "    inp = Input(shape=input_shape)\n",
    "    x = Bidirectional(LSTM(64, return_sequences=True, kernel_regularizer=l2(0.001)))(inp)\n",
    "    x = Dropout(0.5)(x)\n",
    "    x = Bidirectional(LSTM(32, return_sequences=True, kernel_regularizer=l2(0.001)))(x)\n",
    "    x = Dropout(0.5)(x)\n",
    "    x = Attention()(x)\n",
    "    x = Dense(32, activation='relu')(x)\n",
    "    x = Dropout(0.3)(x)\n",
    "    out = Dense(1, activation='linear')(x)\n",
    "    \n",
    "    model = Model(inputs=inp, outputs=out)\n",
    "    model.compile(optimizer=Adam(0.0005), loss='mse', metrics=['mae'])\n",
    "    return model\n",
    "\n",
    "# Keep other models simple for comparison\n",
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
    "    'Bi-LSTM-Attn': build_bilstm_model(input_shape),\n",
    "    '1D-CNN': build_cnn_model(input_shape),\n",
    "    'CNN-LSTM': build_hybrid_model(input_shape)\n",
    "}\n",
    "\n",
    "for name, model in models.items():\n",
    "    print(f\"\\n--- {name} Summary ---\")\n",
    "    model.summary()\n"
]

# Find and replace Cell 10
fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def build_bilstm_model" in source:
            print(f"Found Model Cell at index {i}. Injecting Attention...")
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Added Attention Mechanism.")
else:
    print("Could not find Model Cell.")
