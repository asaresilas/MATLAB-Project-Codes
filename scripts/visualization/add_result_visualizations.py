import json

notebook_path = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/notebooks/02_NASA_DL_training.ipynb'

# Additional result visualization cells
result_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Training History Analysis\n",
            "\n",
            "Visualize the training progress for each model."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Training History Plots\n",
            "fig, axes = plt.subplots(2, 3, figsize=(18, 10))\n",
            "fig.suptitle('Training History for All Models', fontsize=16, fontweight='bold')\n",
            "\n",
            "model_names = list(histories.keys())\n",
            "\n",
            "for idx, name in enumerate(model_names):\n",
            "    history = histories[name]\n",
            "    \n",
            "    # Loss plot\n",
            "    axes[0, idx].plot(history.history['loss'], label='Training Loss', linewidth=2)\n",
            "    axes[0, idx].plot(history.history['val_loss'], label='Validation Loss', linewidth=2)\n",
            "    axes[0, idx].set_title(f'{name} - Loss')\n",
            "    axes[0, idx].set_xlabel('Epoch')\n",
            "    axes[0, idx].set_ylabel('Loss (MSE)')\n",
            "    axes[0, idx].legend()\n",
            "    axes[0, idx].grid(True, alpha=0.3)\n",
            "    \n",
            "    # MAE plot\n",
            "    axes[1, idx].plot(history.history['mae'], label='Training MAE', linewidth=2)\n",
            "    axes[1, idx].plot(history.history['val_mae'], label='Validation MAE', linewidth=2)\n",
            "    axes[1, idx].set_title(f'{name} - MAE')\n",
            "    axes[1, idx].set_xlabel('Epoch')\n",
            "    axes[1, idx].set_ylabel('MAE')\n",
            "    axes[1, idx].legend()\n",
            "    axes[1, idx].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 8. Prediction Analysis\n",
            "\n",
            "Detailed analysis of model predictions vs actual values."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Prediction vs Actual Plots\n",
            "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
            "fig.suptitle('Predictions vs Actual RUL', fontsize=16, fontweight='bold')\n",
            "\n",
            "for idx, name in enumerate(model_names):\n",
            "    y_pred = results[name]['Predictions']\n",
            "    \n",
            "    # Scatter plot\n",
            "    axes[idx].scatter(y_test, y_pred, alpha=0.5, s=20)\n",
            "    axes[idx].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], \n",
            "                   'r--', lw=2, label='Perfect Prediction')\n",
            "    axes[idx].set_title(f'{name}\\nRMSE: {results[name][\"RMSE\"]:.2f}, R²: {results[name][\"R2\"]:.4f}')\n",
            "    axes[idx].set_xlabel('Actual RUL')\n",
            "    axes[idx].set_ylabel('Predicted RUL')\n",
            "    axes[idx].legend()\n",
            "    axes[idx].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Residual Analysis\n",
            "fig, axes = plt.subplots(2, 3, figsize=(18, 10))\n",
            "fig.suptitle('Residual Analysis', fontsize=16, fontweight='bold')\n",
            "\n",
            "for idx, name in enumerate(model_names):\n",
            "    y_pred = results[name]['Predictions']\n",
            "    residuals = y_test - y_pred\n",
            "    \n",
            "    # Residual plot\n",
            "    axes[0, idx].scatter(y_pred, residuals, alpha=0.5, s=20)\n",
            "    axes[0, idx].axhline(y=0, color='r', linestyle='--', lw=2)\n",
            "    axes[0, idx].set_title(f'{name} - Residuals')\n",
            "    axes[0, idx].set_xlabel('Predicted RUL')\n",
            "    axes[0, idx].set_ylabel('Residuals')\n",
            "    axes[0, idx].grid(True, alpha=0.3)\n",
            "    \n",
            "    # Residual distribution\n",
            "    axes[1, idx].hist(residuals, bins=30, edgecolor='black', alpha=0.7)\n",
            "    axes[1, idx].axvline(x=0, color='r', linestyle='--', lw=2)\n",
            "    axes[1, idx].set_title(f'{name} - Residual Distribution')\n",
            "    axes[1, idx].set_xlabel('Residual Value')\n",
            "    axes[1, idx].set_ylabel('Frequency')\n",
            "    axes[1, idx].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Prediction Timeline\n",
            "fig, axes = plt.subplots(3, 1, figsize=(15, 12))\n",
            "fig.suptitle('Prediction Timeline Comparison', fontsize=16, fontweight='bold')\n",
            "\n",
            "for idx, name in enumerate(model_names):\n",
            "    y_pred = results[name]['Predictions']\n",
            "    \n",
            "    axes[idx].plot(y_test, label='Actual RUL', linewidth=2, alpha=0.7)\n",
            "    axes[idx].plot(y_pred, label='Predicted RUL', linewidth=2, alpha=0.7)\n",
            "    axes[idx].fill_between(range(len(y_test)), y_test, y_pred, alpha=0.2)\n",
            "    axes[idx].set_title(f'{name} - Timeline Comparison')\n",
            "    axes[idx].set_xlabel('Test Sample Index')\n",
            "    axes[idx].set_ylabel('RUL (%)')\n",
            "    axes[idx].legend()\n",
            "    axes[idx].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Error Distribution Analysis\n",
            "fig, axes = plt.subplots(1, 2, figsize=(15, 5))\n",
            "fig.suptitle('Error Distribution Comparison', fontsize=16, fontweight='bold')\n",
            "\n",
            "# Absolute Error\n",
            "for name in model_names:\n",
            "    y_pred = results[name]['Predictions']\n",
            "    abs_errors = np.abs(y_test - y_pred)\n",
            "    axes[0].hist(abs_errors, bins=30, alpha=0.5, label=name, edgecolor='black')\n",
            "\n",
            "axes[0].set_title('Absolute Error Distribution')\n",
            "axes[0].set_xlabel('Absolute Error')\n",
            "axes[0].set_ylabel('Frequency')\n",
            "axes[0].legend()\n",
            "axes[0].grid(True, alpha=0.3)\n",
            "\n",
            "# Box plot of errors\n",
            "error_data = [np.abs(y_test - results[name]['Predictions']) for name in model_names]\n",
            "axes[1].boxplot(error_data, labels=model_names)\n",
            "axes[1].set_title('Error Distribution (Box Plot)')\n",
            "axes[1].set_ylabel('Absolute Error')\n",
            "axes[1].grid(True, alpha=0.3)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "# Print summary statistics\n",
            "print(\"\\n=== Error Statistics ===\")\n",
            "for name in model_names:\n",
            "    y_pred = results[name]['Predictions']\n",
            "    abs_errors = np.abs(y_test - y_pred)\n",
            "    print(f\"\\n{name}:\")\n",
            "    print(f\"  Mean Absolute Error: {abs_errors.mean():.2f}\")\n",
            "    print(f\"  Median Absolute Error: {np.median(abs_errors):.2f}\")\n",
            "    print(f\"  Max Absolute Error: {abs_errors.max():.2f}\")\n",
            "    print(f\"  Min Absolute Error: {abs_errors.min():.2f}\")"
        ]
    }
]

# Load notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find position after training (before saving models)
insert_position = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown' and 'Save Models' in ''.join(cell['source']):
        insert_position = i
        break

if insert_position:
    # Insert new cells
    for cell in reversed(result_cells):
        nb['cells'].insert(insert_position, cell)
    
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"Successfully added {len(result_cells)} result visualization cells to the notebook.")
else:
    print("Could not find insertion point. Adding cells at the end instead.")
    nb['cells'].extend(result_cells)
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print(f"Successfully added {len(result_cells)} result visualization cells at the end.")
