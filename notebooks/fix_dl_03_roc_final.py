import json
import os

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\03_Current_Signature_DL_training.ipynb"

def fix_notebook():
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # The new evaluation code
    new_source = [
        "# Evaluation & Comparison\n",
        "from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, auc\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "import numpy as np\n",
        "\n",
        "def evaluate_model(model, X_test, y_test, model_name):\n",
        "    print(f\"--- Evaluating {model_name} ---\")\n",
        "    \n",
        "    # Predictions\n",
        "    y_pred_prob = model.predict(X_test)\n",
        "    y_pred = np.argmax(y_pred_prob, axis=1)\n",
        "    y_true = np.argmax(y_test, axis=1)\n",
        "    \n",
        "    # Classification Report\n",
        "    print(\"Classification Report:\")\n",
        "    print(classification_report(y_true, y_pred, target_names=class_names))\n",
        "    \n",
        "    # Confusion Matrix\n",
        "    cm = confusion_matrix(y_true, y_pred)\n",
        "    plt.figure(figsize=(8, 6))\n",
        "    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)\n",
        "    plt.title(f'Confusion Matrix - {model_name}')\n",
        "    plt.ylabel('True Label')\n",
        "    plt.xlabel('Predicted Label')\n",
        "    plt.show()\n",
        "    \n",
        "    # ROC Curve (Multi-class)\n",
        "    n_classes = y_test.shape[1]\n",
        "    \n",
        "    # Compute ROC curve and ROC area for each class\n",
        "    fpr = dict()\n",
        "    tpr = dict()\n",
        "    roc_auc = dict()\n",
        "    for i in range(n_classes):\n",
        "        fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_pred_prob[:, i])\n",
        "        roc_auc[i] = auc(fpr[i], tpr[i])\n",
        "        \n",
        "    # Compute micro-average ROC curve and ROC area\n",
        "    fpr[\"micro\"], tpr[\"micro\"], _ = roc_curve(y_test.ravel(), y_pred_prob.ravel())\n",
        "    roc_auc[\"micro\"] = auc(fpr[\"micro\"], tpr[\"micro\"])\n",
        "    \n",
        "    # Plot ROC curves\n",
        "    plt.figure(figsize=(10, 8))\n",
        "    plt.plot(fpr[\"micro\"], tpr[\"micro\"],\n",
        "             label='micro-average ROC curve (area = {0:0.2f})'\n",
        "                   ''.format(roc_auc[\"micro\"]),\n",
        "             color='deeppink', linestyle=':', linewidth=4)\n",
        "             \n",
        "    colors = ['aqua', 'darkorange', 'cornflowerblue']\n",
        "    # Ensure we have enough colors if more classes\n",
        "    if len(colors) < n_classes:\n",
        "        colors = sns.color_palette(\"husl\", n_classes)\n",
        "        \n",
        "    for i, color in zip(range(n_classes), colors):\n",
        "        plt.plot(fpr[i], tpr[i], color=color, lw=2,\n",
        "                 label='ROC curve of class {0} (area = {1:0.2f})'\n",
        "                 ''.format(class_names[i]))\n",
        "                 \n",
        "    plt.plot([0, 1], [0, 1], 'k--', lw=2)\n",
        "    plt.xlim([0.0, 1.0])\n",
        "    plt.ylim([0.0, 1.05])\n",
        "    plt.xlabel('False Positive Rate')\n",
        "    plt.ylabel('True Positive Rate')\n",
        "    plt.title(f'Receiver Operating Characteristic (ROC) - {model_name}')\n",
        "    plt.legend(loc=\"lower right\")\n",
        "    plt.show()\n",
        "    \n",
        "    # Calculate Macro Average AUC\n",
        "    try:\n",
        "        macro_roc_auc = roc_auc_score(y_test, y_pred_prob, multi_class='ovr', average='macro')\n",
        "        print(f\"Macro Average ROC AUC: {macro_roc_auc:.4f}\")\n",
        "    except Exception as e:\n",
        "        print(f\"Could not calculate Macro AUC: {e}\")\n",
        "\n",
        "# Evaluate CNN\n",
        "if 'cnn_model' in locals():\n",
        "    evaluate_model(cnn_model, X_test_scaled, y_test, \"CNN Model\")\n",
        "\n",
        "# Evaluate LSTM\n",
        "if 'lstm_model' in locals():\n",
        "    evaluate_model(lstm_model, X_test_scaled, y_test, \"LSTM Model\")\n"
    ]

    found = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            # Identify the cell by its content (PCA visualization)
            if "Skipping CNN feature extraction" in source and "PCA" in source:
                print("Found the PCA visualization cell. Replacing with Evaluation code...")
                cell['source'] = new_source
                # Clear outputs to avoid confusion (and reduce file size)
                cell['outputs'] = []
                cell['execution_count'] = None
                found = True
                break
    
    if found:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print("Notebook updated successfully.")
    else:
        print("Could not find the PCA visualization cell to replace.")

if __name__ == "__main__":
    fix_notebook()
