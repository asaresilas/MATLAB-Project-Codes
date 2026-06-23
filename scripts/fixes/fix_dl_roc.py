"""
Fix ROC Calculation in 02_NASA_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\02_NASA_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New content for the metrics cell
new_source = [
    "from sklearn.metrics import roc_auc_score, roc_curve, accuracy_score\n",
    "\n",
    "print(\"\\n2. Test Set Performance (Generalization):\")\n",
    "print(\"=\"*95)\n",
    "print(f\"{'Model':<15} | {'RMSE (%)':<10} | {'MAE (%)':<10} | {'R² Score':<10} | {'Acc (<10%)':<12} | {'ROC AUC':<10}\")\n",
    "print(\"-\"*95)\n",
    "\n",
    "for name, metrics in results.items():\n",
    "    # Handle missing predictions\n",
    "    if 'Predictions' not in metrics and 'predictions' not in metrics and 'pred' not in metrics:\n",
    "        print(f\"⚠️ Warning: No predictions found for {name}. Keys: {list(metrics.keys())}\")\n",
    "        y_pred = np.zeros_like(y_test) # Dummy\n",
    "    else:\n",
    "        y_pred = metrics.get('Predictions', metrics.get('predictions', metrics.get('pred')))\n",
    "        y_pred = y_pred.flatten()\n",
    "\n",
    "    # Regression Metrics\n",
    "    rmse = metrics['RMSE']\n",
    "    mae = metrics['MAE']\n",
    "    r2 = metrics['R2']\n",
    "    \n",
    "    # Accuracy (<10% Error)\n",
    "    within_10 = np.abs(y_test - y_pred) <= 10\n",
    "    acc_10 = np.mean(within_10) * 100\n",
    "    \n",
    "    # ROC AUC (Binary Classification: Failure if RUL <= 10%)\n",
    "    # We treat low RUL as the 'positive' class (1)\n",
    "    threshold = 10\n",
    "    y_test_binary = (y_test <= threshold).astype(int)\n",
    "    # For predictions, we use the inverted RUL as the 'score' for failure\n",
    "    # Lower RUL = Higher probability of failure\n",
    "    # So we use (100 - y_pred) as the score, or just -y_pred\n",
    "    y_score = -y_pred \n",
    "    \n",
    "    try:\n",
    "        if len(np.unique(y_test_binary)) > 1:\n",
    "            roc = roc_auc_score(y_test_binary, y_score)\n",
    "        else:\n",
    "            roc = 0.5 # Undefined if only one class in test set\n",
    "    except:\n",
    "        roc = 0.5\n",
    "        \n",
    "    print(f\"{name:<15} | {rmse:<10.2f} | {mae:<10.2f} | {r2:<10.4f} | {acc_10:<12.1f} | {roc:<10.4f} %\")\n",
    "print(\"=\"*95)\n"
]

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "from sklearn.metrics import roc_auc_score" in source:
            print(f"Found Metrics Cell at index {i}. Updating ROC logic...")
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Updated ROC calculation.")
else:
    print("Could not find Metrics Cell.")
