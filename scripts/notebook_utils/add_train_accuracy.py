"""
Add train/test accuracy comparison and time-series analysis - Phase 3
"""
import json

# Load notebook
with open('notebooks/02_NASA_ML_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the model training cell and update it to show train accuracy
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and any('TRAIN ML MODELS' in line for line in cell['source']):
        # Update to include train accuracy
        cell['source'] = [
            "# ============================================\n",
            "# TRAIN ML MODELS WITH TRAIN/TEST ACCURACY\n",
            "# ============================================\n",
            "\n",
            "# Initialize models\n",
            "models = {\n",
            "    'Linear Regression': LinearRegression(),\n",
            "    'Random Forest': RandomForestRegressor(\n",
            "        n_estimators=100,\n",
            "        max_depth=20,\n",
            "        min_samples_split=5,\n",
            "        random_state=42,\n",
            "        n_jobs=-1\n",
            "    ),\n",
            "    'Gradient Boosting': GradientBoostingRegressor(\n",
            "        n_estimators=100,\n",
            "        learning_rate=0.1,\n",
            "        max_depth=5,\n",
            "        random_state=42\n",
            "    ),\n",
            "    'SVR': SVR(\n",
            "        kernel='rbf',\n",
            "        C=100,\n",
            "        epsilon=0.1\n",
            "    )\n",
            "}\n",
            "\n",
            "# Train all models and track BOTH train and validation performance\n",
            "trained_models = {}\n",
            "training_results = {}\n",
            "\n",
            "print(\"Training Models on Combined Dataset (All 3 Tests)...\")\n",
            "print(\"=\" * 80)\n",
            "\n",
            "for name, model in models.items():\n",
            "    print(f\"\\n{name}:\")\n",
            "    print(\"-\" * 40)\n",
            "    \n",
            "    # Train model\n",
            "    model.fit(X_train_scaled, y_train)\n",
            "    \n",
            "    # Predict on TRAINING set (to check overfitting)\n",
            "    y_train_pred = model.predict(X_train_scaled)\n",
            "    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))\n",
            "    train_mae = mean_absolute_error(y_train, y_train_pred)\n",
            "    train_r2 = r2_score(y_train, y_train_pred)\n",
            "    \n",
            "    # Predict on VALIDATION set\n",
            "    y_val_pred = model.predict(X_val_scaled)\n",
            "    val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))\n",
            "    val_mae = mean_absolute_error(y_val, y_val_pred)\n",
            "    val_r2 = r2_score(y_val, y_val_pred)\n",
            "    \n",
            "    # Store results\n",
            "    trained_models[name] = model\n",
            "    training_results[name] = {\n",
            "        'Train_RMSE': train_rmse,\n",
            "        'Train_MAE': train_mae,\n",
            "        'Train_R2': train_r2,\n",
            "        'Val_RMSE': val_rmse,\n",
            "        'Val_MAE': val_mae,\n",
            "        'Val_R2': val_r2,\n",
            "        'Overfit_Gap': val_rmse - train_rmse  # Positive = overfitting\n",
            "    }\n",
            "    \n",
            "    # Print results\n",
            "    print(f\"  TRAINING Performance:\")\n",
            "    print(f\"    RMSE: {train_rmse:6.2f}%\")\n",
            "    print(f\"    MAE:  {train_mae:6.2f}%\")\n",
            "    print(f\"    R²:   {train_r2:7.4f}\")\n",
            "    \n",
            "    print(f\"\\n  VALIDATION Performance:\")\n",
            "    print(f\"    RMSE: {val_rmse:6.2f}%\")\n",
            "    print(f\"    MAE:  {val_mae:6.2f}%\")\n",
            "    print(f\"    R²:   {val_r2:7.4f}\")\n",
            "    \n",
            "    print(f\"\\n  Overfitting Check:\")\n",
            "    gap = val_rmse - train_rmse\n",
            "    if gap < 5:\n",
            "        status = \"✓ Good (minimal overfitting)\"\n",
            "    elif gap < 10:\n",
            "        status = \"⚠ Moderate overfitting\"\n",
            "    else:\n",
            "        status = \"✗ High overfitting!\"\n",
            "    print(f\"    Gap (Val - Train): {gap:+.2f}% {status}\")\n",
            "\n",
            "print(\"\\n\" + \"=\" * 80)\n",
            "print(\"✓ All models trained!\")\n"
        ]
        print(f"Updated cell {i}: Model training with train/val accuracy")
        break

# Save
with open('notebooks/02_NASA_ML_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("\nPhase 3: Added train/validation accuracy comparison")
print("✓ Models now show both training and validation performance")
print("✓ Overfitting check included (gap between train and val RMSE)")
