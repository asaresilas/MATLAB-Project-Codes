"""
Update performance metrics cell in 02_NASA_DL_training.ipynb to include Train/Val Loss
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cell content (Expanded)
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
    "for name, metrics in test_results.items():\n",
    "    # Calculate Accuracy (within 10% threshold)\n",
    "    y_pred = metrics['predictions']\n",
    "    y_test_safe = np.where(y_test == 0, 1e-6, y_test)\n",
    "    relative_error = np.abs((y_test - y_pred) / y_test_safe)\n",
    "    accuracy_within_10 = np.mean(relative_error < 0.10) * 100\n",
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
    "    # Simple status check\n",
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

# Replace the last cell (which we just added)
nb['cells'][-1]['source'] = new_source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Updated performance metrics cell with Train/Val data.")
