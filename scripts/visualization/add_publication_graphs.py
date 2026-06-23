"""
Add publication-quality visualizations to 06_Induction_Motor_DL_training.ipynb
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# ===== 1. ADD SIGNAL VISUALIZATION CELL (after data loading) =====
signal_viz_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "### Signal Visualization for Publication\n",
        "import matplotlib.pyplot as plt\n",
        "import numpy as np\n",
        "\n",
        "# Plot sample signals from each class\n",
        "fig, axes = plt.subplots(7, 2, figsize=(16, 20))\n",
        "fig.suptitle('Raw Signal Samples by Class (Channel 1 & 2)', fontsize=16, fontweight='bold')\n",
        "\n",
        "for class_idx in range(7):\n",
        "    # Find first sample of this class\n",
        "    class_samples = np.where(y == class_idx)[0]\n",
        "    if len(class_samples) > 0:\n",
        "        sample_idx = class_samples[0]\n",
        "        signal = X[sample_idx]\n",
        "        \n",
        "        # Plot Channel 1\n",
        "        axes[class_idx, 0].plot(signal[:, 0], linewidth=0.5, color='#1f77b4')\n",
        "        axes[class_idx, 0].set_title(f'Class {class_idx} - Channel 1', fontweight='bold')\n",
        "        axes[class_idx, 0].set_ylabel('Amplitude')\n",
        "        axes[class_idx, 0].grid(alpha=0.3)\n",
        "        \n",
        "        # Plot Channel 2\n",
        "        axes[class_idx, 1].plot(signal[:, 1], linewidth=0.5, color='#ff7f0e')\n",
        "        axes[class_idx, 1].set_title(f'Class {class_idx} - Channel 2', fontweight='bold')\n",
        "        axes[class_idx, 1].set_ylabel('Amplitude')\n",
        "        axes[class_idx, 1].grid(alpha=0.3)\n",
        "\n",
        "axes[-1, 0].set_xlabel('Time Steps', fontsize=12)\n",
        "axes[-1, 1].set_xlabel('Time Steps', fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n"
    ]
}

# ===== 2. ADD FREQUENCY DOMAIN ANALYSIS CELL =====
fft_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "### Frequency Domain Analysis\n",
        "from scipy.fft import fft, fftfreq\n",
        "\n",
        "fig, axes = plt.subplots(7, 2, figsize=(16, 20))\n",
        "fig.suptitle('Frequency Spectrum by Class (Channel 1 & 2)', fontsize=16, fontweight='bold')\n",
        "\n",
        "for class_idx in range(7):\n",
        "    class_samples = np.where(y == class_idx)[0]\n",
        "    if len(class_samples) > 0:\n",
        "        sample_idx = class_samples[0]\n",
        "        signal = X[sample_idx]\n",
        "        \n",
        "        # FFT for Channel 1\n",
        "        fft_vals = np.abs(fft(signal[:, 0]))\n",
        "        freqs = fftfreq(len(signal[:, 0]), 1.0)\n",
        "        axes[class_idx, 0].plot(freqs[:len(freqs)//2], fft_vals[:len(fft_vals)//2], linewidth=0.8, color='#2ca02c')\n",
        "        axes[class_idx, 0].set_title(f'Class {class_idx} - Channel 1 FFT', fontweight='bold')\n",
        "        axes[class_idx, 0].set_ylabel('Magnitude')\n",
        "        axes[class_idx, 0].grid(alpha=0.3)\n",
        "        \n",
        "        # FFT for Channel 2\n",
        "        fft_vals = np.abs(fft(signal[:, 1]))\n",
        "        axes[class_idx, 1].plot(freqs[:len(freqs)//2], fft_vals[:len(fft_vals)//2], linewidth=0.8, color='#d62728')\n",
        "        axes[class_idx, 1].set_title(f'Class {class_idx} - Channel 2 FFT', fontweight='bold')\n",
        "        axes[class_idx, 1].set_ylabel('Magnitude')\n",
        "        axes[class_idx, 1].grid(alpha=0.3)\n",
        "\n",
        "axes[-1, 0].set_xlabel('Frequency (Hz)', fontsize=12)\n",
        "axes[-1, 1].set_xlabel('Frequency (Hz)', fontsize=12)\n",
        "plt.tight_layout()\n",
        "plt.show()\n"
    ]
}

# ===== 3. ADD ENHANCED CONFUSION MATRIX CELL (after training) =====
enhanced_cm_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "### Enhanced Confusion Matrix with Percentages\n",
        "from sklearn.metrics import confusion_matrix, classification_report\n",
        "import seaborn as sns\n",
        "\n",
        "# Get predictions\n",
        "y_pred = cnn_model.predict(X_test)\n",
        "y_pred_classes = np.argmax(y_pred, axis=1)\n",
        "y_test_classes = np.argmax(y_test, axis=1)\n",
        "\n",
        "# Confusion matrix\n",
        "cm = confusion_matrix(y_test_classes, y_pred_classes)\n",
        "cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100\n",
        "\n",
        "# Plot\n",
        "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))\n",
        "\n",
        "# Absolute counts\n",
        "sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1, cbar_kws={'label': 'Count'})\n",
        "ax1.set_title('Confusion Matrix (Counts)', fontsize=14, fontweight='bold')\n",
        "ax1.set_xlabel('Predicted Class', fontsize=12)\n",
        "ax1.set_ylabel('True Class', fontsize=12)\n",
        "ax1.set_xticklabels([f'Class {i}' for i in range(7)])\n",
        "ax1.set_yticklabels([f'Class {i}' for i in range(7)])\n",
        "\n",
        "# Percentages\n",
        "sns.heatmap(cm_percent, annot=True, fmt='.1f', cmap='Greens', ax=ax2, cbar_kws={'label': 'Percentage (%)'})\n",
        "ax2.set_title('Confusion Matrix (Percentages)', fontsize=14, fontweight='bold')\n",
        "ax2.set_xlabel('Predicted Class', fontsize=12)\n",
        "ax2.set_ylabel('True Class', fontsize=12)\n",
        "ax2.set_xticklabels([f'Class {i}' for i in range(7)])\n",
        "ax2.set_yticklabels([f'Class {i}' for i in range(7)])\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# Print classification report\n",
        "print(\"\\n\" + \"=\"*60)\n",
        "print(\"CLASSIFICATION REPORT\")\n",
        "print(\"=\"*60)\n",
        "print(classification_report(y_test_classes, y_pred_classes, target_names=[f'Class {i}' for i in range(7)]))\n"
    ]
}

# ===== 4. ADD PER-CLASS PERFORMANCE METRICS =====
per_class_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "### Per-Class Performance Metrics\n",
        "from sklearn.metrics import precision_recall_fscore_support\n",
        "\n",
        "precision, recall, f1, support = precision_recall_fscore_support(y_test_classes, y_pred_classes)\n",
        "\n",
        "# Create bar plots\n",
        "fig, axes = plt.subplots(2, 2, figsize=(16, 12))\n",
        "fig.suptitle('Per-Class Performance Metrics', fontsize=16, fontweight='bold')\n",
        "\n",
        "classes = [f'Class {i}' for i in range(7)]\n",
        "x = np.arange(len(classes))\n",
        "\n",
        "# Precision\n",
        "axes[0, 0].bar(x, precision, color='#1f77b4', alpha=0.8)\n",
        "axes[0, 0].set_title('Precision by Class', fontweight='bold', fontsize=12)\n",
        "axes[0, 0].set_ylabel('Precision', fontsize=11)\n",
        "axes[0, 0].set_xticks(x)\n",
        "axes[0, 0].set_xticklabels(classes, rotation=45)\n",
        "axes[0, 0].set_ylim([0, 1.1])\n",
        "axes[0, 0].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(precision):\n",
        "    axes[0, 0].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')\n",
        "\n",
        "# Recall\n",
        "axes[0, 1].bar(x, recall, color='#ff7f0e', alpha=0.8)\n",
        "axes[0, 1].set_title('Recall by Class', fontweight='bold', fontsize=12)\n",
        "axes[0, 1].set_ylabel('Recall', fontsize=11)\n",
        "axes[0, 1].set_xticks(x)\n",
        "axes[0, 1].set_xticklabels(classes, rotation=45)\n",
        "axes[0, 1].set_ylim([0, 1.1])\n",
        "axes[0, 1].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(recall):\n",
        "    axes[0, 1].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')\n",
        "\n",
        "# F1-Score\n",
        "axes[1, 0].bar(x, f1, color='#2ca02c', alpha=0.8)\n",
        "axes[1, 0].set_title('F1-Score by Class', fontweight='bold', fontsize=12)\n",
        "axes[1, 0].set_ylabel('F1-Score', fontsize=11)\n",
        "axes[1, 0].set_xticks(x)\n",
        "axes[1, 0].set_xticklabels(classes, rotation=45)\n",
        "axes[1, 0].set_ylim([0, 1.1])\n",
        "axes[1, 0].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(f1):\n",
        "    axes[1, 0].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')\n",
        "\n",
        "# Support (sample count)\n",
        "axes[1, 1].bar(x, support, color='#d62728', alpha=0.8)\n",
        "axes[1, 1].set_title('Test Samples by Class', fontweight='bold', fontsize=12)\n",
        "axes[1, 1].set_ylabel('Number of Samples', fontsize=11)\n",
        "axes[1, 1].set_xticks(x)\n",
        "axes[1, 1].set_xticklabels(classes, rotation=45)\n",
        "axes[1, 1].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(support):\n",
        "    axes[1, 1].text(i, v + max(support)*0.02, f'{int(v)}', ha='center', fontweight='bold')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n"
    ]
}

# ===== 5. ADD ROC CURVES =====
roc_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "### ROC Curves for Multi-Class Classification\n",
        "from sklearn.metrics import roc_curve, auc\n",
        "from sklearn.preprocessing import label_binarize\n",
        "\n",
        "# Binarize for ROC\n",
        "y_test_bin = label_binarize(y_test_classes, classes=range(7))\n",
        "\n",
        "# Compute ROC curve and AUC for each class\n",
        "fpr = dict()\n",
        "tpr = dict()\n",
        "roc_auc = dict()\n",
        "\n",
        "for i in range(7):\n",
        "    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_pred[:, i])\n",
        "    roc_auc[i] = auc(fpr[i], tpr[i])\n",
        "\n",
        "# Plot\n",
        "plt.figure(figsize=(12, 10))\n",
        "colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']\n",
        "\n",
        "for i, color in zip(range(7), colors):\n",
        "    plt.plot(fpr[i], tpr[i], color=color, lw=2.5,\n",
        "             label=f'Class {i} (AUC = {roc_auc[i]:.3f})')\n",
        "\n",
        "plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random Classifier')\n",
        "plt.xlim([0.0, 1.0])\n",
        "plt.ylim([0.0, 1.05])\n",
        "plt.xlabel('False Positive Rate', fontsize=13, fontweight='bold')\n",
        "plt.ylabel('True Positive Rate', fontsize=13, fontweight='bold')\n",
        "plt.title('ROC Curves - Multi-Class Classification', fontsize=15, fontweight='bold')\n",
        "plt.legend(loc=\"lower right\", fontsize=11)\n",
        "plt.grid(alpha=0.3)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# Print AUC scores\n",
        "print(\"\\n\" + \"=\"*60)\n",
        "print(\"AUC SCORES BY CLASS\")\n",
        "print(\"=\"*60)\n",
        "for i in range(7):\n",
        "    print(f\"Class {i}: {roc_auc[i]:.4f}\")\n",
        "print(f\"\\nMean AUC: {np.mean(list(roc_auc.values())):.4f}\")\n"
    ]
}

# Find insertion points and add cells
print("Adding visualization cells to notebook...")

# Insert signal viz after data loading (after Cell 3)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if "X = data_signals[:min_len]" in source:
            nb['cells'].insert(i + 1, signal_viz_cell)
            nb['cells'].insert(i + 2, fft_cell)
            print(f"Added signal and FFT visualization cells after cell {i}")
            break

# Insert enhanced metrics after training
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if "history_cnn = cnn_model.fit(" in source:
            nb['cells'].insert(i + 1, enhanced_cm_cell)
            nb['cells'].insert(i + 2, per_class_cell)
            nb['cells'].insert(i + 3, roc_cell)
            print(f"Added performance visualization cells after cell {i}")
            break

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("\nNotebook saved with publication-quality visualizations!")
print("\nAdded graphs:")
print("  1. Raw signal samples (7 classes × 2 channels)")
print("  2. Frequency spectrum analysis (FFT)")
print("  3. Enhanced confusion matrices (counts + percentages)")
print("  4. Per-class metrics (Precision, Recall, F1, Support)")
print("  5. ROC curves with AUC scores")
