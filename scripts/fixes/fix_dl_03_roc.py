"""
Fix ROC Calculation in 03_Current_Signature_DL_training.ipynb (Multi-Class)
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New content for the metrics cell
# We need to ensure we have probabilities for ROC AUC
new_source = [
    "from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score\n",
    "from sklearn.preprocessing import label_binarize\n",
    "\n",
    "print(\"\\n--- Model Evaluation ---\")\n",
    "\n",
    "for name, model in models.items():\n",
    "    print(f\"\\nEvaluating {name}...\")\n",
    "    \n",
    "    # Get Predictions (Probabilities)\n",
    "    y_pred_prob = model.predict(X_test)\n",
    "    y_pred = np.argmax(y_pred_prob, axis=1)\n",
    "    y_true = np.argmax(y_test, axis=1)\n",
    "    \n",
    "    # Accuracy\n",
    "    acc = accuracy_score(y_true, y_pred)\n",
    "    print(f\"Accuracy: {acc*100:.2f}%\")\n",
    "    \n",
    "    # ROC AUC (Multi-Class)\n",
    "    try:\n",
    "        # Check if binary or multi-class\n",
    "        if y_test.shape[1] == 2:\n",
    "             # Binary case\n",
    "             roc = roc_auc_score(y_test[:, 1], y_pred_prob[:, 1])\n",
    "        else:\n",
    "             # Multi-class case (One-vs-Rest)\n",
    "             roc = roc_auc_score(y_test, y_pred_prob, multi_class='ovr', average='macro')\n",
    "        print(f\"ROC AUC: {roc:.4f}\")\n",
    "    except Exception as e:\n",
    "        print(f\"ROC AUC: Could not calculate ({e})\")\n",
    "        \n",
    "    # Confusion Matrix\n",
    "    cm = confusion_matrix(y_true, y_pred)\n",
    "    plt.figure(figsize=(6, 5))\n",
    "    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')\n",
    "    plt.title(f'{name} Confusion Matrix')\n",
    "    plt.ylabel('True Label')\n",
    "    plt.xlabel('Predicted Label')\n",
    "    plt.show()\n",
    "    \n",
    "    print(\"Classification Report:\")\n",
    "    print(classification_report(y_true, y_pred))\n"
]

fixed = False
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        # Look for the evaluation loop
        if "for name, model in models.items():" in source and "confusion_matrix" in source:
            print(f"Found Evaluation Cell at index {i}. Updating ROC logic for Multi-Class...")
            cell['source'] = new_source
            fixed = True
            break

if fixed:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print("Notebook saved. Updated ROC calculation for Multi-Class.")
else:
    print("Could not find Evaluation Cell.")
