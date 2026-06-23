"""
Add Accuracy Plotting Cell to 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New Plotting Cell
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ============================================\n",
        "# PLOT ACCURACY PER MODEL\n",
        "# ============================================\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "import numpy as np\n",
        "\n",
        "model_names = []\n",
        "accuracies = []\n",
        "\n",
        "for name, metrics in results.items():\n",
        "    if 'Predictions' in metrics or 'predictions' in metrics or 'pred' in metrics:\n",
        "        y_pred = metrics.get('Predictions', metrics.get('predictions', metrics.get('pred'))).flatten()\n",
        "        # Accuracy (<10% Error)\n",
        "        within_10 = np.abs(y_test - y_pred) <= 10\n",
        "        acc = np.mean(within_10) * 100\n",
        "        model_names.append(name)\n",
        "        accuracies.append(acc)\n",
        "\n",
        "plt.figure(figsize=(10, 6))\n",
        "bars = plt.bar(model_names, accuracies, color=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c'])\n",
        "\n",
        "plt.title('Prognostic Accuracy (<10% Error) by Model', fontsize=16, fontweight='bold')\n",
        "plt.ylabel('Accuracy (%)', fontsize=12)\n",
        "plt.ylim(0, 105)\n",
        "plt.grid(axis='y', alpha=0.3)\n",
        "\n",
        "# Add labels\n",
        "for bar in bars:\n",
        "    height = bar.get_height()\n",
        "    plt.text(bar.get_x() + bar.get_width()/2., height + 1,\n",
        "             f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')\n",
        "\n",
        "plt.show()"
    ]
}

# Append to the end of the notebook
nb['cells'].append(new_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Notebook saved. Added Accuracy Plotting Cell.")
