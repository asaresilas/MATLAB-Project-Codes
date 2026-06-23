"""
Debug KeyError and check USE_SUBSET in 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# 1. Modify last cell to debug keys
last_cell = nb['cells'][-1]
source = last_cell['source']

# Create a robust version of the loop
new_source = [
    "# ============================================\n",
    "# DETAILED NUMERICAL PERFORMANCE REPORT\n",
    "# ============================================\n",
    "\n",
    "print(\"1. Test Set Performance (Generalization):\")\n",
    "print(\"=\" * 95)\n",
    "print(f\"{'Model':<15} | {'RMSE (%)':<10} | {'MAE (%)':<10} | {'R² Score':<10} | {'Acc (<10%)':<12}\")\n",
    "print(\"-\" * 95)\n",
    "\n",
    "for name, metrics in results.items():\n",
    "    # DEBUG: Print keys if first time\n",
    "    # print(f\"Debug: Keys for {name}: {list(metrics.keys())}\")\n",
    "    \n",
    "    # Try to get predictions with multiple key variations\n",
    "    y_pred = metrics.get('Predictions', metrics.get('predictions', metrics.get('pred', None)))\n",
    "    \n",
    "    if y_pred is None:\n",
    "        print(f\"⚠️ Warning: No predictions found for {name}. Keys: {list(metrics.keys())}\")\n",
    "        accuracy_within_10 = 0.0\n",
    "    else:\n",
    "        # Calculate Accuracy (within 10% threshold)\n",
    "        y_test_safe = np.where(y_test == 0, 1e-6, y_test)\n",
    "        relative_error = np.abs((y_test - y_pred) / y_test_safe)\n",
    "        accuracy_within_10 = np.mean(relative_error < 0.10) * 100\n",
    "    \n",
    "    print(f\"{name:<15} | {metrics['RMSE']:<10.2f} | {metrics['MAE']:<10.2f} | {metrics['R2']:<10.4f} | {accuracy_within_10:<12.1f}%\")\n",
    "\n",
    "print(\"=\" * 95)\n",
    "print(\"\\n2. Training vs Validation (Overfitting Check):\")\n",
    "print(\"=\" * 95)\n",
    "print(f\"{'Model':<15} | {'Final Train Loss':<18} | {'Final Val Loss':<18} | {'Status':<15}\")\n",
    "print(\"-\" * 95)\n",
    "\n",
    "for name in histories.keys():\n",
    "    history = histories[name].history\n",
    "    train_loss = history['loss'][-1]\n",
    "    val_loss = history['val_loss'][-1]\n",
    "    \n",
    "    if val_loss > train_loss * 1.5:\n",
    "        status = \"Overfitting ⚠️\"\n",
    "    elif val_loss < train_loss:\n",
    "        status = \"Good (Under) ✅\"\n",
    "    else:\n",
    "        status = \"Good ✅\"\n",
    "        \n",
    "    print(f\"{name:<15} | {train_loss:<18.4f} | {val_loss:<18.4f} | {status:<15}\")\n",
    "print(\"=\" * 95)\n"
]

nb['cells'][-1]['source'] = new_source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Updated last cell with robust key handling.")

# 2. Check USE_SUBSET
print("\n=== CHECKING USE_SUBSET ===")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "USE_SUBSET" in source:
            print(f"Cell {i}:")
            print(source.strip())
