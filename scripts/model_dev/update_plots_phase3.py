"""
Update final prediction visualization cell - Phase 3
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Cell: Comprehensive Prediction Visualizations - split into separate figures
prediction_viz_code = [
    "# ============================================\n",
    "# PREDICTION VISUALIZATIONS\n",
    "# ============================================\n",
    "\n",
    "# Use best model for detailed visualization\n",
    "best_model = trained_models[best_test_model]\n",
    "y_pred_best = test_results[best_test_model]['predictions']\n",
    "\n",
    "print(f\"Creating visualizations for: {best_test_model}\\n\")\n",
    "\n",
    "# 1. Actual vs Predicted (all models)\n",
    "plt.figure(figsize=(12, 10))\n",
    "colors = ['blue', 'green', 'orange', 'purple']\n",
    "for idx, name in enumerate(trained_models.keys()):\n",
    "    y_pred = test_results[name]['predictions']\n",
    "    plt.scatter(y_test, y_pred, alpha=0.6, s=40, label=name, color=colors[idx % len(colors)])\n",
    "plt.plot([0, 100], [0, 100], 'k--', lw=3, label='Perfect Prediction', alpha=0.7)\n",
    "plt.xlabel('Actual RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('Predicted RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.title('Actual vs Predicted RUL - All Models', fontsize=15, fontweight='bold')\n",
    "plt.legend(fontsize=11, loc='upper left')\n",
    "plt.grid(True, alpha=0.4)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# 2. Time-series prediction (best model only)\n",
    "plt.figure(figsize=(16, 6))\n",
    "test_indices = np.arange(len(y_test))\n",
    "plt.plot(test_indices, y_test, 'b-', linewidth=2.5, label='Actual RUL', alpha=0.8)\n",
    "plt.plot(test_indices, y_pred_best, 'r--', linewidth=2.5, label='Predicted RUL', alpha=0.8)\n",
    "plt.fill_between(test_indices, y_test, y_pred_best, alpha=0.2, color='gray', label='Prediction Error')\n",
    "plt.xlabel('Test Sample Index (Time)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.title(f'RUL Prediction Over Time - {best_test_model}', fontsize=15, fontweight='bold')\n",
    "plt.legend(fontsize=12, loc='upper right')\n",
    "plt.grid(True, alpha=0.4)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# 3. Error distribution\n",
    "errors = y_test - y_pred_best\n",
    "plt.figure(figsize=(14, 6))\n",
    "plt.hist(errors, bins=50, edgecolor='black', alpha=0.7, color='coral')\n",
    "plt.axvline(x=0, color='red', linestyle='--', linewidth=2.5, label='Zero Error (Perfect)')\n",
    "plt.axvline(x=errors.mean(), color='green', linestyle='--', linewidth=2.5, \n",
    "            label=f'Mean Error: {errors.mean():.2f}%')\n",
    "plt.xlabel('Prediction Error (Actual - Predicted) %', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('Frequency', fontsize=13, fontweight='bold')\n",
    "plt.title(f'Error Distribution - {best_test_model}', fontsize=15, fontweight='bold')\n",
    "plt.legend(fontsize=12)\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# 4. Residual plot\n",
    "plt.figure(figsize=(14, 6))\n",
    "plt.scatter(y_pred_best, errors, alpha=0.5, s=50, c=y_test, cmap='viridis', edgecolors='black', linewidth=0.5)\n",
    "plt.axhline(y=0, color='red', linestyle='--', linewidth=2.5, label='Zero Residual')\n",
    "plt.xlabel('Predicted RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('Residual (Actual - Predicted) %', fontsize=13, fontweight='bold')\n",
    "plt.title(f'Residual Plot - {best_test_model}', fontsize=15, fontweight='bold')\n",
    "plt.legend(fontsize=12)\n",
    "plt.grid(True, alpha=0.4)\n",
    "cbar = plt.colorbar()\n",
    "cbar.set_label('Actual RUL (%)', fontsize=12, fontweight='bold')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# 5. Absolute error vs RUL\n",
    "abs_errors = np.abs(errors)\n",
    "plt.figure(figsize=(14, 6))\n",
    "scatter = plt.scatter(y_test, abs_errors, alpha=0.6, s=50, c=y_test, cmap='coolwarm', \n",
    "                     edgecolors='black', linewidth=0.5)\n",
    "plt.xlabel('Actual RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('Absolute Error (%)', fontsize=13, fontweight='bold')\n",
    "plt.title(f'Absolute Error vs RUL - {best_test_model}', fontsize=15, fontweight='bold')\n",
    "plt.grid(True, alpha=0.4)\n",
    "cbar = plt.colorbar(scatter)\n",
    "cbar.set_label('RUL (%)', fontsize=12, fontweight='bold')\n",
    "# Add trend line\n",
    "z = np.polyfit(y_test, abs_errors, 1)\n",
    "p = np.poly1d(z)\n",
    "plt.plot(sorted(y_test), p(sorted(y_test)), \"r--\", linewidth=2, alpha=0.7, label='Trend Line')\n",
    "plt.legend(fontsize=11)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# Print error statistics\n",
    "print(f\"\\n{'='*60}\")\n",
    "print(f\"Error Statistics for {best_test_model}:\")\n",
    "print(f\"{'='*60}\")\n",
    "print(f\"  Mean Error:     {errors.mean():8.2f}%\")\n",
    "print(f\"  Std Error:      {errors.std():8.2f}%\")\n",
    "print(f\"  Max Error:      {errors.max():8.2f}%\")\n",
    "print(f\"  Min Error:      {errors.min():8.2f}%\")\n",
    "print(f\"  Mean Abs Error: {abs_errors.mean():8.2f}%\")\n",
    "print(f\"{'='*60}\")\n"
]

# Update the cell
updated = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        if any('PREDICTION VISUALIZATIONS' in line for line in cell['source']):
            nb['cells'][i]['source'] = prediction_viz_code
            print("Updated: Comprehensive Prediction Visualizations")
            updated = True
            break

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

if updated:
    print("\nPhase 3 complete: Updated prediction analysis visualization")
    print("\n" + "="*60)
    print("ALL VISUALIZATIONS UPDATED!")
    print("="*60)
    print("\nSummary of changes:")
    print("  ✓ Vibration signals: 3 separate figures (one per time point)")
    print("  ✓ RUL plot: Enhanced standalone figure")
    print("  ✓ Data split: Enhanced standalone figure")
    print("  ✓ Feature scaling: 2 separate figures (before/after)")
    print("  ✓ Model comparison: 3 separate figures (RMSE, MAE, R²)")
    print("  ✓ Prediction analysis: 5 separate figures")
    print("\nTotal: 14 individual figures with legends and better formatting!")
else:
    print("Warning: Prediction visualization cell not found")
