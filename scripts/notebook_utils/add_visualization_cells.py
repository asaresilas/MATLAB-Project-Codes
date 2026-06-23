"""
Add evaluation and visualization cells to comparison notebook
"""
import json

nb_path = 'notebooks/03_NASA_DL_Models_Comparison.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    # Cell: RUL Conversion
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Practical RUL Conversion\n",
            "\n",
            "We convert the percentage RUL into practical time units for reporting."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "def convert_rul_units(rul_percentage, total_life_minutes=10000):\n",
            "    \"\"\"Convert RUL % to various time units. Assumes approx 10,000 mins total life for demo.\"\"\"\n",
            "    remaining_mins = (rul_percentage / 100) * total_life_minutes\n",
            "    return {\n",
            "        'Hours': remaining_mins / 60,\n",
            "        'Days': remaining_mins / (60 * 24),\n",
            "        'Weeks': remaining_mins / (60 * 24 * 7),\n",
            "        'Months': remaining_mins / (60 * 24 * 30),\n",
            "        'Years': remaining_mins / (60 * 24 * 365)\n",
            "    }\n",
            "\n",
            "# Example conversion for the last prediction of the best model\n",
            "best_model_name = min(results, key=lambda k: results[k]['RMSE'])\n",
            "last_pred_pct = results[best_model_name]['Predictions'][-1]\n",
            "converted = convert_rul_units(last_pred_pct)\n",
            "\n",
            "print(f\"\\n--- Practical RUL Estimates ({best_model_name}) ---\")\n",
            "print(f\"Current RUL: {last_pred_pct:.2f}%\")\n",
            "for unit, value in converted.items():\n",
            "    print(f\"  {value:.2f} {unit}\")"
        ]
    },
    # Cell: Visualization
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6. Publication-Quality Visualizations\n",
            "\n",
            "Comparing model performance and visualizing predictions."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# 1. Model Comparison Bar Chart\n",
            "metrics_df = pd.DataFrame(results).T[['RMSE', 'MAE', 'R2']]\n",
            "\n",
            "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
            "metrics = ['RMSE', 'MAE', 'R2']\n",
            "colors = ['#FF9999', '#66B2FF', '#99FF99']\n",
            "\n",
            "for i, metric in enumerate(metrics):\n",
            "    sns.barplot(x=metrics_df.index, y=metrics_df[metric], ax=axes[i], palette=[colors[i]]*3)\n",
            "    axes[i].set_title(f'{metric} Comparison (Lower is Better)' if metric != 'R2' else f'{metric} Comparison (Higher is Better)')\n",
            "    axes[i].set_ylabel(metric)\n",
            "    for p in axes[i].patches:\n",
            "        axes[i].annotate(f'{p.get_height():.2f}', (p.get_x() + p.get_width() / 2., p.get_height()), \n",
            "                         ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontweight='bold')\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "# 2. Actual vs Predicted RUL (Best Model)\n",
            "best_pred = results[best_model_name]['Predictions']\n",
            "\n",
            "plt.figure(figsize=(15, 6))\n",
            "plt.plot(y_test, label='Actual RUL', color='black', linewidth=2.5, alpha=0.8)\n",
            "plt.plot(best_pred, label=f'Predicted RUL ({best_model_name})', color='dodgerblue', linewidth=2, linestyle='--')\n",
            "plt.title(f'Best Model Prediction: {best_model_name}', fontsize=16, fontweight='bold')\n",
            "plt.xlabel('Time Steps (Test Set)', fontsize=12)\n",
            "plt.ylabel('RUL (%)', fontsize=12)\n",
            "plt.legend(fontsize=12)\n",
            "plt.grid(True, alpha=0.3)\n",
            "plt.show()\n",
            "\n",
            "# 3. Error Distribution\n",
            "plt.figure(figsize=(10, 5))\n",
            "errors = y_test - best_pred\n",
            "sns.histplot(errors, kde=True, color='purple', bins=30)\n",
            "plt.title(f'Error Distribution ({best_model_name})', fontsize=14)\n",
            "plt.xlabel('Prediction Error (Actual - Predicted)', fontsize=12)\n",
            "plt.ylabel('Frequency', fontsize=12)\n",
            "plt.grid(True, alpha=0.3)\n",
            "plt.show()"
        ]
    }
]

nb['cells'].extend(new_cells)

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Added evaluation and visualization cells.")
