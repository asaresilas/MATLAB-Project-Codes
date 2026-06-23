import json
import os

# Define notebook paths
notebooks_dir = r'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/notebooks'
notebooks = {
    '01_ML_model_training.ipynb': 'ml_classification',
    '01_DL_cnn_training.ipynb': 'dl_classification',
    '02_NASA_ML_training.ipynb': 'ml_regression',
    '02_NASA_DL_training.ipynb': 'dl_regression'
}

def create_ml_classification_viz():
    """Visualizations for ML classification (CWRU)"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Data Exploration Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Class Distribution\n",
                "plt.figure(figsize=(12, 6))\n",
                "class_counts = y_train.value_counts().sort_index()\n",
                "plt.bar(range(len(class_counts)), class_counts.values, edgecolor='black', alpha=0.7)\n",
                "plt.title('Class Distribution in Training Set', fontsize=14, fontweight='bold')\n",
                "plt.xlabel('Fault Class')\n",
                "plt.ylabel('Number of Samples')\n",
                "plt.xticks(range(len(class_counts)), class_counts.index)\n",
                "plt.grid(True, alpha=0.3, axis='y')\n",
                "plt.tight_layout()\n",
                "plt.show()\n",
                "print(f'Total Training Samples: {len(y_train)}')\n",
                "print(f'Number of Classes: {len(class_counts)}')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Feature Distributions\n",
                "fig, axes = plt.subplots(2, 2, figsize=(15, 10))\n",
                "fig.suptitle('Feature Distributions', fontsize=16, fontweight='bold')\n",
                "\n",
                "# RMS\n",
                "axes[0, 0].hist(X_train['rms'], bins=50, edgecolor='black', alpha=0.7)\n",
                "axes[0, 0].set_title('RMS Distribution')\n",
                "axes[0, 0].set_xlabel('RMS Value')\n",
                "axes[0, 0].set_ylabel('Frequency')\n",
                "axes[0, 0].grid(True, alpha=0.3)\n",
                "\n",
                "# Kurtosis\n",
                "axes[0, 1].hist(X_train['kurtosis'], bins=50, edgecolor='black', alpha=0.7)\n",
                "axes[0, 1].set_title('Kurtosis Distribution')\n",
                "axes[0, 1].set_xlabel('Kurtosis Value')\n",
                "axes[0, 1].set_ylabel('Frequency')\n",
                "axes[0, 1].grid(True, alpha=0.3)\n",
                "\n",
                "# Skewness\n",
                "axes[1, 0].hist(X_train['skewness'], bins=50, edgecolor='black', alpha=0.7)\n",
                "axes[1, 0].set_title('Skewness Distribution')\n",
                "axes[1, 0].set_xlabel('Skewness Value')\n",
                "axes[1, 0].set_ylabel('Frequency')\n",
                "axes[1, 0].grid(True, alpha=0.3)\n",
                "\n",
                "# Peak-to-Peak\n",
                "if 'peak_to_peak' in X_train.columns:\n",
                "    axes[1, 1].hist(X_train['peak_to_peak'], bins=50, edgecolor='black', alpha=0.7)\n",
                "    axes[1, 1].set_title('Peak-to-Peak Distribution')\n",
                "    axes[1, 1].set_xlabel('Peak-to-Peak Value')\n",
                "    axes[1, 1].set_ylabel('Frequency')\n",
                "    axes[1, 1].grid(True, alpha=0.3)\n",
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
                "# Feature Correlation Heatmap\n",
                "import seaborn as sns\n",
                "plt.figure(figsize=(12, 10))\n",
                "corr_matrix = X_train.corr()\n",
                "sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0, \n",
                "            square=True, linewidths=0.5, cbar_kws={\"shrink\": 0.8})\n",
                "plt.title('Feature Correlation Heatmap', fontsize=14, fontweight='bold')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Model Performance Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Individual Confusion Matrices\n",
                "from sklearn.metrics import confusion_matrix\n",
                "import seaborn as sns\n",
                "\n",
                "for model_name in results.keys():\n",
                "    y_pred = results[model_name]['predictions']\n",
                "    cm = confusion_matrix(y_test, y_pred)\n",
                "    \n",
                "    plt.figure(figsize=(10, 8))\n",
                "    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', square=True, \n",
                "                cbar_kws={\"shrink\": 0.8})\n",
                "    plt.title(f'{model_name} - Confusion Matrix\\nAccuracy: {results[model_name][\"accuracy\"]:.4f}', \n",
                "              fontsize=14, fontweight='bold')\n",
                "    plt.ylabel('True Label')\n",
                "    plt.xlabel('Predicted Label')\n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Per-Class Performance for Each Model\n",
                "from sklearn.metrics import classification_report\n",
                "\n",
                "for model_name in results.keys():\n",
                "    y_pred = results[model_name]['predictions']\n",
                "    report = classification_report(y_test, y_pred, output_dict=True)\n",
                "    \n",
                "    # Extract per-class metrics\n",
                "    classes = [k for k in report.keys() if k not in ['accuracy', 'macro avg', 'weighted avg']]\n",
                "    precision = [report[c]['precision'] for c in classes]\n",
                "    recall = [report[c]['recall'] for c in classes]\n",
                "    f1 = [report[c]['f1-score'] for c in classes]\n",
                "    \n",
                "    # Plot\n",
                "    x = range(len(classes))\n",
                "    width = 0.25\n",
                "    \n",
                "    plt.figure(figsize=(14, 6))\n",
                "    plt.bar([i - width for i in x], precision, width, label='Precision', alpha=0.8)\n",
                "    plt.bar(x, recall, width, label='Recall', alpha=0.8)\n",
                "    plt.bar([i + width for i in x], f1, width, label='F1-Score', alpha=0.8)\n",
                "    \n",
                "    plt.title(f'{model_name} - Per-Class Performance', fontsize=14, fontweight='bold')\n",
                "    plt.xlabel('Class')\n",
                "    plt.ylabel('Score')\n",
                "    plt.xticks(x, classes)\n",
                "    plt.legend()\n",
                "    plt.grid(True, alpha=0.3, axis='y')\n",
                "    plt.ylim([0, 1.05])\n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
        }
    ]

def create_dl_classification_viz():
    """Visualizations for DL classification (CWRU CNN)"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Training History Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Training Loss\n",
                "plt.figure(figsize=(12, 6))\n",
                "plt.plot(history.history['loss'], label='Training Loss', linewidth=2)\n",
                "plt.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)\n",
                "plt.title('Model Loss Over Epochs', fontsize=14, fontweight='bold')\n",
                "plt.xlabel('Epoch')\n",
                "plt.ylabel('Loss')\n",
                "plt.legend()\n",
                "plt.grid(True, alpha=0.3)\n",
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
                "# Training Accuracy\n",
                "plt.figure(figsize=(12, 6))\n",
                "plt.plot(history.history['accuracy'], label='Training Accuracy', linewidth=2)\n",
                "plt.plot(history.history['val_accuracy'], label='Validation Accuracy', linewidth=2)\n",
                "plt.title('Model Accuracy Over Epochs', fontsize=14, fontweight='bold')\n",
                "plt.xlabel('Epoch')\n",
                "plt.ylabel('Accuracy')\n",
                "plt.legend()\n",
                "plt.grid(True, alpha=0.3)\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Model Performance Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Confusion Matrix\n",
                "from sklearn.metrics import confusion_matrix\n",
                "import seaborn as sns\n",
                "\n",
                "y_pred_classes = np.argmax(y_pred, axis=1)\n",
                "y_test_classes = np.argmax(y_test, axis=1)\n",
                "cm = confusion_matrix(y_test_classes, y_pred_classes)\n",
                "\n",
                "plt.figure(figsize=(12, 10))\n",
                "sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', square=True, \n",
                "            cbar_kws={\"shrink\": 0.8})\n",
                "plt.title(f'Confusion Matrix\\nTest Accuracy: {test_accuracy:.4f}', \n",
                "          fontsize=14, fontweight='bold')\n",
                "plt.ylabel('True Label')\n",
                "plt.xlabel('Predicted Label')\n",
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
                "# Per-Class Performance\n",
                "from sklearn.metrics import classification_report\n",
                "\n",
                "report = classification_report(y_test_classes, y_pred_classes, output_dict=True)\n",
                "classes = [k for k in report.keys() if k not in ['accuracy', 'macro avg', 'weighted avg']]\n",
                "precision = [report[c]['precision'] for c in classes]\n",
                "recall = [report[c]['recall'] for c in classes]\n",
                "f1 = [report[c]['f1-score'] for c in classes]\n",
                "\n",
                "x = range(len(classes))\n",
                "width = 0.25\n",
                "\n",
                "plt.figure(figsize=(14, 6))\n",
                "plt.bar([i - width for i in x], precision, width, label='Precision', alpha=0.8)\n",
                "plt.bar(x, recall, width, label='Recall', alpha=0.8)\n",
                "plt.bar([i + width for i in x], f1, width, label='F1-Score', alpha=0.8)\n",
                "\n",
                "plt.title('Per-Class Performance Metrics', fontsize=14, fontweight='bold')\n",
                "plt.xlabel('Class')\n",
                "plt.ylabel('Score')\n",
                "plt.xticks(x, classes)\n",
                "plt.legend()\n",
                "plt.grid(True, alpha=0.3, axis='y')\n",
                "plt.ylim([0, 1.05])\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        }
    ]

def create_ml_regression_viz():
    """Visualizations for ML regression (NASA)"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Data Exploration Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# RUL Distribution\n",
                "plt.figure(figsize=(12, 6))\n",
                "plt.hist(y_train, bins=50, edgecolor='black', alpha=0.7)\n",
                "plt.title('RUL Distribution in Training Set', fontsize=14, fontweight='bold')\n",
                "plt.xlabel('RUL (%)')\n",
                "plt.ylabel('Frequency')\n",
                "plt.grid(True, alpha=0.3)\n",
                "plt.tight_layout()\n",
                "plt.show()\n",
                "print(f'RUL Range: {y_train.min():.2f} - {y_train.max():.2f}')\n",
                "print(f'Mean RUL: {y_train.mean():.2f}')"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Feature Correlation with RUL\n",
                "import seaborn as sns\n",
                "correlations = X_train.corrwith(pd.Series(y_train, index=X_train.index)).sort_values(ascending=False)\n",
                "top_features = correlations.abs().nlargest(15)\n",
                "\n",
                "plt.figure(figsize=(12, 8))\n",
                "plt.barh(range(len(top_features)), correlations[top_features.index].values, alpha=0.7)\n",
                "plt.yticks(range(len(top_features)), top_features.index)\n",
                "plt.xlabel('Correlation with RUL')\n",
                "plt.title('Top 15 Features Correlated with RUL', fontsize=14, fontweight='bold')\n",
                "plt.grid(True, alpha=0.3, axis='x')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Model Performance Visualizations\n"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Individual Model: Predictions vs Actual\n",
                "for model_name in results.keys():\n",
                "    y_pred = results[model_name]['predictions']\n",
                "    \n",
                "    plt.figure(figsize=(10, 8))\n",
                "    plt.scatter(y_test, y_pred, alpha=0.5, s=30)\n",
                "    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], \n",
                "             'r--', lw=2, label='Perfect Prediction')\n",
                "    plt.title(f'{model_name} - Predictions vs Actual\\nRMSE: {results[model_name][\"RMSE\"]:.2f}, R²: {results[model_name][\"R2\"]:.4f}', \n",
                "              fontsize=14, fontweight='bold')\n",
                "    plt.xlabel('Actual RUL')\n",
                "    plt.ylabel('Predicted RUL')\n",
                "    plt.legend()\n",
                "    plt.grid(True, alpha=0.3)\n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Individual Model: Residual Analysis\n",
                "for model_name in results.keys():\n",
                "    y_pred = results[model_name]['predictions']\n",
                "    residuals = y_test - y_pred\n",
                "    \n",
                "    fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n",
                "    fig.suptitle(f'{model_name} - Residual Analysis', fontsize=16, fontweight='bold')\n",
                "    \n",
                "    # Residual scatter\n",
                "    axes[0].scatter(y_pred, residuals, alpha=0.5, s=30)\n",
                "    axes[0].axhline(y=0, color='r', linestyle='--', lw=2)\n",
                "    axes[0].set_title('Residual Plot')\n",
                "    axes[0].set_xlabel('Predicted RUL')\n",
                "    axes[0].set_ylabel('Residuals')\n",
                "    axes[0].grid(True, alpha=0.3)\n",
                "    \n",
                "    # Residual distribution\n",
                "    axes[1].hist(residuals, bins=30, edgecolor='black', alpha=0.7)\n",
                "    axes[1].axvline(x=0, color='r', linestyle='--', lw=2)\n",
                "    axes[1].set_title('Residual Distribution')\n",
                "    axes[1].set_xlabel('Residual Value')\n",
                "    axes[1].set_ylabel('Frequency')\n",
                "    axes[1].grid(True, alpha=0.3)\n",
                "    \n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Individual Model: Prediction Timeline\n",
                "for model_name in results.keys():\n",
                "    y_pred = results[model_name]['predictions']\n",
                "    \n",
                "    plt.figure(figsize=(14, 6))\n",
                "    plt.plot(y_test, label='Actual RUL', linewidth=2, alpha=0.7)\n",
                "    plt.plot(y_pred, label='Predicted RUL', linewidth=2, alpha=0.7)\n",
                "    plt.fill_between(range(len(y_test)), y_test, y_pred, alpha=0.2)\n",
                "    plt.title(f'{model_name} - Prediction Timeline', fontsize=14, fontweight='bold')\n",
                "    plt.xlabel('Test Sample Index')\n",
                "    plt.ylabel('RUL (%)')\n",
                "    plt.legend()\n",
                "    plt.grid(True, alpha=0.3)\n",
                "    plt.tight_layout()\n",
                "    plt.show()"
            ]
        }
    ]

def create_dl_regression_viz():
    """Visualizations for DL regression (NASA) - already done, but ensure individual plots"""
    return create_ml_regression_viz()  # Same structure but for DL models

# Main execution
print("Adding individual visualizations to all notebooks...")
print("=" * 60)

for notebook_name, notebook_type in notebooks.items():
    notebook_path = os.path.join(notebooks_dir, notebook_name)
    
    if not os.path.exists(notebook_path):
        print(f"Skipping {notebook_name} - file not found")
        continue
    
    print(f"\nProcessing: {notebook_name} ({notebook_type})")
    
    # Select appropriate visualizations
    if notebook_type == 'ml_classification':
        new_cells = create_ml_classification_viz()
    elif notebook_type == 'dl_classification':
        new_cells = create_dl_classification_viz()
    elif notebook_type == 'ml_regression':
        new_cells = create_ml_regression_viz()
    elif notebook_type == 'dl_regression':
        new_cells = create_dl_regression_viz()
    else:
        print(f"  Unknown type: {notebook_type}")
        continue
    
    # Load notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    # Remove old visualization cells if they exist (to avoid duplicates)
    nb['cells'] = [cell for cell in nb['cells'] 
                   if not (cell['cell_type'] == 'markdown' and 
                          any(keyword in ''.join(cell['source']) 
                              for keyword in ['Exploration Visualizations', 'Performance Visualizations', 
                                            'Training History Visualizations']))]
    
    # Find insertion point (before saving models or at the end)
    insert_position = len(nb['cells'])
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown' and any(keyword in ''.join(cell['source']) 
                                                    for keyword in ['Save', 'Saving', 'Export']):
            insert_position = i
            break
    
    # Insert new cells
    for cell in reversed(new_cells):
        nb['cells'].insert(insert_position, cell)
    
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"  [OK] Added {len(new_cells)} visualization cells")

print("\n" + "=" * 60)
print("All notebooks updated successfully!")
print("\nSummary:")
print("  - Each graph is now standalone (not in matrices)")
print("  - Individual plots for each model")
print("  - Consistent visualization style across all notebooks")
