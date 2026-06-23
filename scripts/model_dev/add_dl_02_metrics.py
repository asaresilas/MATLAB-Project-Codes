"""
Append performance metrics cell to 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cell content
new_source = [
    "# ============================================\n",
    "# DETAILED PERFORMANCE METRICS\n",
    "# ============================================\n",
    "\n",
    "print(\"Detailed Performance Metrics (Test Set):\")\n",
    "print(\"=\" * 80)\n",
    "print(f\"{'Model':<15} | {'RMSE (%)':<10} | {'MAE (%)':<10} | {'R² Score':<10} | {'Acc (<10%)':<12}\")\n",
    "print(\"-\" * 80)\n",
    "\n",
    "for name, metrics in test_results.items():\n",
    "    # Calculate Accuracy (within 10% threshold)\n",
    "    y_pred = metrics['predictions']\n",
    "    # Avoid division by zero\n",
    "    y_test_safe = np.where(y_test == 0, 1e-6, y_test)\n",
    "    relative_error = np.abs((y_test - y_pred) / y_test_safe)\n",
    "    accuracy_within_10 = np.mean(relative_error < 0.10) * 100\n",
    "    \n",
    "    print(f\"{name:<15} | {metrics['RMSE']:<10.2f} | {metrics['MAE']:<10.2f} | {metrics['R2']:<10.4f} | {accuracy_within_10:<12.1f}%\")\n",
    "\n",
    "print(\"=\" * 80)\n",
    "print(\"Note: 'Acc (<10%)' represents the percentage of predictions within 10% of the actual RUL.\")\n"
]

# Create new code cell
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": new_source
}

# Append to notebook
nb['cells'].append(new_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("Appended performance metrics cell.")
