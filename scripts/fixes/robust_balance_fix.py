"""
Replace the data balance analysis cell with a more robust version that handles any number of classes
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and replace the entire data balance analysis cell
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'DATA BALANCE ANALYSIS' in source and 'Counter(y_train)' in source:
            print(f"Found data balance cell at index {i}")
            
            # Replace with robust version
            new_cell_source = """# ===== DATA BALANCE ANALYSIS =====
from collections import Counter
import numpy as np

print("\\n" + "="*60)
print("CLASS DISTRIBUTION ANALYSIS")
print("="*60)

# Automatically detect number of classes
unique_classes = np.unique(np.concatenate([y_train, y_test]))
num_classes = len(unique_classes)
print(f"\\nDetected {num_classes} unique classes: {unique_classes}")

# Generate class names dynamically
class_names = {cls: f'Class {cls}' for cls in unique_classes}

# Count classes
train_counts = Counter(y_train)
test_counts = Counter(y_test)

print("\\nTraining Set Distribution:")
for cls in sorted(train_counts.keys()):
    print(f"  {class_names[cls]}: {train_counts[cls]} samples ({train_counts[cls]/len(y_train)*100:.1f}%)")

print("\\nTest Set Distribution:")
for cls in sorted(test_counts.keys()):
    print(f"  {class_names[cls]}: {test_counts[cls]} samples ({test_counts[cls]/len(y_test)*100:.1f}%)")

# Visualize distribution
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Training set
train_labels = [class_names[i] for i in sorted(train_counts.keys())]
train_values = [train_counts[i] for i in sorted(train_counts.keys())]
colors = plt.cm.viridis(np.linspace(0, 1, len(train_labels)))
axes[0].bar(train_labels, train_values, color=colors, alpha=0.8)
axes[0].set_title('Training Set Class Distribution', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Class', fontsize=12)
axes[0].set_ylabel('Number of Samples', fontsize=12)
axes[0].grid(axis='y', alpha=0.3)
axes[0].tick_params(axis='x', rotation=45)
for i, v in enumerate(train_values):
    axes[0].text(i, v + max(train_values)*0.02, str(v), ha='center', fontweight='bold')

# Test set
test_labels = [class_names[i] for i in sorted(test_counts.keys())]
test_values = [test_counts[i] for i in sorted(test_counts.keys())]
axes[1].bar(test_labels, test_values, color=colors, alpha=0.8)
axes[1].set_title('Test Set Class Distribution', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Class', fontsize=12)
axes[1].set_ylabel('Number of Samples', fontsize=12)
axes[1].grid(axis='y', alpha=0.3)
axes[1].tick_params(axis='x', rotation=45)
for i, v in enumerate(test_values):
    axes[1].text(i, v + max(test_values)*0.02, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.show()

# Check for imbalance
max_count = max(train_counts.values())
min_count = min(train_counts.values())
imbalance_ratio = max_count / min_count

print(f"\\nImbalance Ratio: {imbalance_ratio:.2f}:1")
if imbalance_ratio > 3:
    print("WARNING: Significant class imbalance detected!")
    print("   Consider using SMOTE, class weights, or balanced sampling.")
else:
    print("Classes are relatively balanced.")
"""
            
            nb['cells'][i]['source'] = new_cell_source.split('\n')
            print("Replaced data balance cell with robust version")
            break

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=2)

print("\nNotebook saved with robust data balance analysis!")
print("This version automatically detects the number of classes and won't crash.")
