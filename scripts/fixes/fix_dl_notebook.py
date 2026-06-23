"""
Fix 06_Induction_Motor_DL_training.ipynb with same improvements as ML notebook
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

# Load notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Processing DL notebook with {len(nb['cells'])} cells...")

# 1. ADD DATA BALANCE ANALYSIS CELL
# Find the cell that does train/test split
split_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'train_test_split' in source or 'X_train' in source:
            split_cell_idx = i
            print(f"Found train/test split at cell {i}")
            break

if split_cell_idx is None:
    print("WARNING: Could not find train/test split cell!")
    split_cell_idx = 5  # Default position

balance_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ===== DATA BALANCE ANALYSIS =====\n",
        "from collections import Counter\n",
        "\n",
        "print(\"\\n\" + \"=\"*60)\n",
        "print(\"CLASS DISTRIBUTION ANALYSIS\")\n",
        "print(\"=\"*60)\n",
        "\n",
        "# Class names\n",
        "class_names = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']\n",
        "\n",
        "# Count classes\n",
        "train_counts = Counter(y_train)\n",
        "test_counts = Counter(y_test)\n",
        "\n",
        "print(\"\\nTraining Set Distribution:\")\n",
        "for cls in sorted(train_counts.keys()):\n",
        "    print(f\"  Class {cls} ({class_names[cls]}): {train_counts[cls]} samples ({train_counts[cls]/len(y_train)*100:.1f}%)\")\n",
        "\n",
        "print(\"\\nTest Set Distribution:\")\n",
        "for cls in sorted(test_counts.keys()):\n",
        "    print(f\"  Class {cls} ({class_names[cls]}): {test_counts[cls]} samples ({test_counts[cls]/len(y_test)*100:.1f}%)\")\n",
        "\n",
        "# Visualize distribution\n",
        "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
        "\n",
        "# Training set\n",
        "train_labels = [class_names[i] for i in sorted(train_counts.keys())]\n",
        "train_values = [train_counts[i] for i in sorted(train_counts.keys())]\n",
        "axes[0].bar(train_labels, train_values, color=['green', 'orange', 'red', 'darkred'], alpha=0.7)\n",
        "axes[0].set_title('Training Set Class Distribution', fontsize=14, fontweight='bold')\n",
        "axes[0].set_xlabel('Class', fontsize=12)\n",
        "axes[0].set_ylabel('Number of Samples', fontsize=12)\n",
        "axes[0].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(train_values):\n",
        "    axes[0].text(i, v + max(train_values)*0.02, str(v), ha='center', fontweight='bold')\n",
        "\n",
        "# Test set\n",
        "test_labels = [class_names[i] for i in sorted(test_counts.keys())]\n",
        "test_values = [test_counts[i] for i in sorted(test_counts.keys())]\n",
        "axes[1].bar(test_labels, test_values, color=['green', 'orange', 'red', 'darkred'], alpha=0.7)\n",
        "axes[1].set_title('Test Set Class Distribution', fontsize=14, fontweight='bold')\n",
        "axes[1].set_xlabel('Class', fontsize=12)\n",
        "axes[1].set_ylabel('Number of Samples', fontsize=12)\n",
        "axes[1].grid(axis='y', alpha=0.3)\n",
        "for i, v in enumerate(test_values):\n",
        "    axes[1].text(i, v + max(test_values)*0.02, str(v), ha='center', fontweight='bold')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "# Check for imbalance\n",
        "max_count = max(train_counts.values())\n",
        "min_count = min(train_counts.values())\n",
        "imbalance_ratio = max_count / min_count\n",
        "\n",
        "print(f\"\\nImbalance Ratio: {imbalance_ratio:.2f}:1\")\n",
        "if imbalance_ratio > 3:\n",
        "    print(\"WARNING: Significant class imbalance detected!\")\n",
        "    print(\"   Consider using class weights in model.fit() or SMOTE.\")\n",
        "else:\n",
        "    print(\"Classes are relatively balanced.\")\n"
    ]
}

# Insert after split cell
nb['cells'].insert(split_cell_idx + 1, balance_cell)
print(f"Added balance analysis cell at position {split_cell_idx + 1}")

# 2. FIX PLOTS WITHOUT LEGENDS
fixes_made = 0
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Fix confusion matrix or classification report plots
        if 'confusion_matrix' in source.lower() and 'heatmap' in source:
            if 'xticklabels' in source and 'np.unique' in source:
                new_source = source.replace(
                    "xticklabels=np.unique(y_test)",
                    "xticklabels=['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']"
                ).replace(
                    "yticklabels=np.unique(y_test)",
                    "yticklabels=['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']"
                )
                nb['cells'][i]['source'] = new_source.split('\n')
                print(f"Fixed confusion matrix labels in cell {i}")
                fixes_made += 1

# Save modified notebook
output_path = notebook_path.replace('.ipynb', '_fixed.ipynb')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print(f"\nFixed DL notebook saved to: {output_path}")
print(f"Total fixes applied: {fixes_made + 1}")  # +1 for balance cell
print("\nChanges made:")
print("1. Added data balance analysis cell with visualization")
print("2. Added imbalance ratio calculation")
if fixes_made > 0:
    print(f"3. Fixed {fixes_made} plot(s) with proper class labels")
