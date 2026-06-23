"""
Add Custom Accuracy Metric and Plotting to 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Add Custom Metric Definition
metric_source = [
    "import tensorflow.keras.backend as K\n",
    "\n",
    "def accuracy_10_percent(y_true, y_pred):\n",
    "    diff = K.abs(y_true - y_pred)\n",
    "    return K.mean(K.less_equal(diff, 10.0))\n",
    "\n"
]

# Inject metric definition before model building
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def build_bilstm_model" in source:
            cell['source'] = metric_source + cell['source']
            # Update compile statement to use the new metric
            new_source = []
            for line in cell['source']:
                if "model.compile" in line:
                    new_source.append("    model.compile(optimizer=Adam(0.0005), loss='mse', metrics=['mae', accuracy_10_percent])\n")
                else:
                    new_source.append(line)
            cell['source'] = new_source
            break

# 2. Add Plotting Cell for Accuracy History
plot_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ============================================\n",
        "# PLOT TRAINING vs VALIDATION ACCURACY\n",
        "# ============================================\n",
        "plt.figure(figsize=(15, 5))\n",
        "\n",
        "for i, (name, history) in enumerate(histories.items()):\n",
        "    plt.subplot(1, 3, i+1)\n",
        "    plt.plot(history.history['accuracy_10_percent'], label='Train Acc')\n",
        "    plt.plot(history.history['val_accuracy_10_percent'], label='Val Acc')\n",
        "    plt.title(f'{name} Accuracy (<10% Error)')\n",
        "    plt.xlabel('Epoch')\n",
        "    plt.ylabel('Accuracy')\n",
        "    plt.legend()\n",
        "    plt.grid(True, alpha=0.3)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
}

# Append plotting cell
nb['cells'].append(plot_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved. Added Custom Accuracy Metric and History Plot.")
