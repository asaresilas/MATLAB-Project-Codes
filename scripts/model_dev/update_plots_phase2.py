"""
Update remaining visualization cells in NASA notebook - Phase 2
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Cell: Train/Val/Test Split visualization
split_viz_code = [
    "# ============================================\n",
    "# TRAIN-VALIDATION-TEST SPLIT (TEMPORAL)\n",
    "# ============================================\n",
    "\n",
    "# Separate features and target\n",
    "X = features_df.drop('RUL', axis=1).values  # Features\n",
    "y = features_df['RUL'].values                # Target (RUL)\n",
    "\n",
    "# Calculate split indices (temporal order preserved)\n",
    "n_samples = len(X)\n",
    "train_end = int(0.6 * n_samples)\n",
    "val_end = int(0.8 * n_samples)\n",
    "\n",
    "# Split data\n",
    "X_train = X[:train_end]\n",
    "y_train = y[:train_end]\n",
    "\n",
    "X_val = X[train_end:val_end]\n",
    "y_val = y[train_end:val_end]\n",
    "\n",
    "X_test = X[val_end:]\n",
    "y_test = y[val_end:]\n",
    "\n",
    "print(\"Dataset Split (Temporal):\")\n",
    "print(f\"  Training:   {X_train.shape[0]} samples ({X_train.shape[0]/n_samples*100:.1f}%)\")\n",
    "print(f\"  Validation: {X_val.shape[0]} samples ({X_val.shape[0]/n_samples*100:.1f}%)\")\n",
    "print(f\"  Test:       {X_test.shape[0]} samples ({X_test.shape[0]/n_samples*100:.1f}%)\")\n",
    "\n",
    "print(\"\\nRUL Distribution:\")\n",
    "print(f\"  Train - Mean RUL: {y_train.mean():.2f}%, Range: [{y_train.min():.1f}, {y_train.max():.1f}]\")\n",
    "print(f\"  Val   - Mean RUL: {y_val.mean():.2f}%, Range: [{y_val.min():.1f}, {y_val.max():.1f}]\")\n",
    "print(f\"  Test  - Mean RUL: {y_test.mean():.2f}%, Range: [{y_test.min():.1f}, {y_test.max():.1f}]\")\n",
    "\n",
    "# Visualize split\n",
    "plt.figure(figsize=(16, 6))\n",
    "plt.plot(y, label='RUL Over Time', linewidth=2.5, color='darkblue', alpha=0.8)\n",
    "plt.axvline(x=train_end, color='green', linestyle='--', linewidth=2.5, label='Train/Val Split', alpha=0.8)\n",
    "plt.axvline(x=val_end, color='orange', linestyle='--', linewidth=2.5, label='Val/Test Split', alpha=0.8)\n",
    "\n",
    "# Add shaded regions\n",
    "plt.axvspan(0, train_end, alpha=0.1, color='green', label='Training Set')\n",
    "plt.axvspan(train_end, val_end, alpha=0.1, color='orange', label='Validation Set')\n",
    "plt.axvspan(val_end, n_samples, alpha=0.1, color='red', label='Test Set')\n",
    "\n",
    "plt.xlabel('Sample Index (Time)', fontsize=13, fontweight='bold')\n",
    "plt.ylabel('RUL (%)', fontsize=13, fontweight='bold')\n",
    "plt.title('Temporal Data Split for Time-Series RUL Prediction', fontsize=15, fontweight='bold')\n",
    "plt.legend(fontsize=11, loc='upper right')\n",
    "plt.grid(True, alpha=0.4)\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell: Feature Scaling visualization - split into 2 separate figures
scaling_viz_code = [
    "# ============================================\n",
    "# FEATURE SCALING\n",
    "# ============================================\n",
    "\n",
    "# Initialize scaler\n",
    "scaler = StandardScaler()\n",
    "\n",
    "# Fit on training data ONLY (to avoid data leakage)\n",
    "scaler.fit(X_train)\n",
    "\n",
    "# Transform all sets using the same scaler\n",
    "X_train_scaled = scaler.transform(X_train)\n",
    "X_val_scaled = scaler.transform(X_val)\n",
    "X_test_scaled = scaler.transform(X_test)\n",
    "\n",
    "print(\"Feature Scaling Complete!\")\n",
    "print(f\"\\nScaled Training Data:\")\n",
    "print(f\"  Mean: {X_train_scaled.mean(axis=0).mean():.6f} (should be ≈0)\")\n",
    "print(f\"  Std:  {X_train_scaled.std(axis=0).mean():.6f} (should be ≈1)\")\n",
    "\n",
    "# Visualize scaling effect on first feature\n",
    "feature_idx = 0\n",
    "feature_name = features_df.columns[feature_idx]\n",
    "\n",
    "# Before scaling\n",
    "plt.figure(figsize=(14, 6))\n",
    "plt.hist(X_train[:, feature_idx], bins=50, edgecolor='black', alpha=0.7, color='steelblue')\n",
    "plt.title(f'Before Scaling: {feature_name}', fontsize=14, fontweight='bold')\n",
    "plt.xlabel('Value', fontsize=12, fontweight='bold')\n",
    "plt.ylabel('Frequency', fontsize=12, fontweight='bold')\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "plt.axvline(X_train[:, feature_idx].mean(), color='red', linestyle='--', \n",
    "            linewidth=2, label=f'Mean = {X_train[:, feature_idx].mean():.4f}')\n",
    "plt.legend(fontsize=11)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# After scaling\n",
    "plt.figure(figsize=(14, 6))\n",
    "plt.hist(X_train_scaled[:, feature_idx], bins=50, edgecolor='black', alpha=0.7, color='green')\n",
    "plt.title(f'After Scaling: {feature_name}', fontsize=14, fontweight='bold')\n",
    "plt.xlabel('Scaled Value', fontsize=12, fontweight='bold')\n",
    "plt.ylabel('Frequency', fontsize=12, fontweight='bold')\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "plt.axvline(X_train_scaled[:, feature_idx].mean(), color='red', linestyle='--', \n",
    "            linewidth=2, label=f'Mean = {X_train_scaled[:, feature_idx].mean():.4f}')\n",
    "plt.legend(fontsize=11)\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell: Model Comparison - separate figures for each metric
comparison_viz_code = [
    "# ============================================\n",
    "# COMPARE MODEL PERFORMANCE\n",
    "# ============================================\n",
    "\n",
    "# Create comparison DataFrame\n",
    "results_df = pd.DataFrame(training_results).T\n",
    "results_df = results_df.sort_values('RMSE')  # Sort by RMSE (lower is better)\n",
    "\n",
    "print(\"Model Performance Comparison (Validation Set):\")\n",
    "print(\"=\" * 60)\n",
    "display(results_df.style.background_gradient(cmap='RdYlGn_r', subset=['RMSE', 'MAE'])\n",
    "                        .background_gradient(cmap='RdYlGn', subset=['R2']))\n",
    "\n",
    "# RMSE comparison\n",
    "plt.figure(figsize=(12, 6))\n",
    "bars = plt.bar(results_df.index, results_df['RMSE'], color='coral', edgecolor='black', linewidth=1.5)\n",
    "plt.title('RMSE Comparison (Lower is Better)', fontsize=14, fontweight='bold')\n",
    "plt.ylabel('RMSE (%)', fontsize=12, fontweight='bold')\n",
    "plt.xlabel('Model', fontsize=12, fontweight='bold')\n",
    "plt.xticks(rotation=45, ha='right')\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "# Add value labels on bars\n",
    "for bar in bars:\n",
    "    height = bar.get_height()\n",
    "    plt.text(bar.get_x() + bar.get_width()/2., height,\n",
    "             f'{height:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# MAE comparison\n",
    "plt.figure(figsize=(12, 6))\n",
    "bars = plt.bar(results_df.index, results_df['MAE'], color='skyblue', edgecolor='black', linewidth=1.5)\n",
    "plt.title('MAE Comparison (Lower is Better)', fontsize=14, fontweight='bold')\n",
    "plt.ylabel('MAE (%)', fontsize=12, fontweight='bold')\n",
    "plt.xlabel('Model', fontsize=12, fontweight='bold')\n",
    "plt.xticks(rotation=45, ha='right')\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "for bar in bars:\n",
    "    height = bar.get_height()\n",
    "    plt.text(bar.get_x() + bar.get_width()/2., height,\n",
    "             f'{height:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# R² comparison\n",
    "plt.figure(figsize=(12, 6))\n",
    "bars = plt.bar(results_df.index, results_df['R2'], color='lightgreen', edgecolor='black', linewidth=1.5)\n",
    "plt.axhline(y=0.8, color='red', linestyle='--', linewidth=2, label='Good Threshold (0.8)', alpha=0.7)\n",
    "plt.title('R² Score Comparison (Higher is Better)', fontsize=14, fontweight='bold')\n",
    "plt.ylabel('R² Score', fontsize=12, fontweight='bold')\n",
    "plt.xlabel('Model', fontsize=12, fontweight='bold')\n",
    "plt.xticks(rotation=45, ha='right')\n",
    "plt.legend(fontsize=11)\n",
    "plt.grid(True, alpha=0.3, axis='y')\n",
    "for bar in bars:\n",
    "    height = bar.get_height()\n",
    "    plt.text(bar.get_x() + bar.get_width()/2., height,\n",
    "             f'{height:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# Identify best model\n",
    "best_model_name = results_df.index[0]\n",
    "print(f\"\\n🏆 Best Model: {best_model_name}\")\n",
    "print(f\"   RMSE: {results_df.loc[best_model_name, 'RMSE']:.2f}%\")\n",
    "print(f\"   R²:   {results_df.loc[best_model_name, 'R2']:.4f}\")\n"
]

# Update cells
updated_count = 0
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        # Train/Val/Test Split
        if any('TRAIN-VALIDATION-TEST SPLIT' in line for line in cell['source']):
            nb['cells'][i]['source'] = split_viz_code
            print("Updated: Train/Val/Test Split visualization")
            updated_count += 1
        
        # Feature Scaling
        elif any('FEATURE SCALING' in line and 'scaler = StandardScaler()' in ''.join(cell['source']) for line in cell['source']):
            nb['cells'][i]['source'] = scaling_viz_code
            print("Updated: Feature Scaling visualization")
            updated_count += 1
        
        # Model Comparison
        elif any('COMPARE MODEL PERFORMANCE' in line for line in cell['source']):
            nb['cells'][i]['source'] = comparison_viz_code
            print("Updated: Model Comparison visualization")
            updated_count += 1

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print(f"\nPhase 2 complete: Updated {updated_count} visualization cells")
