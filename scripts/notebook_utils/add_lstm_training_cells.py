"""
Add training, evaluation, and comparison cells to notebook
"""
import json

# Load notebook
with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    # Cell: Markdown - Training
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Train Model\n",
            "\n",
            "We use callbacks to ensure optimal training:\n",
            "- **EarlyStopping**: Stop if validation loss doesn't improve (prevents overfitting).\n",
            "- **ModelCheckpoint**: Save the best model.\n",
            "- **ReduceLROnPlateau**: Lower learning rate if stuck.\n"
        ]
    },
    
    # Cell: Code - Training Loop
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ============================================\n",
            "# TRAIN MODEL\n",
            "# ============================================\n",
            "\n",
            "callbacks = [\n",
            "    EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1),\n",
            "    ModelCheckpoint('best_lstm_model.keras', monitor='val_loss', save_best_only=True, verbose=1),\n",
            "    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5, verbose=1)\n",
            "]\n",
            "\n",
            "history = model.fit(\n",
            "    X_train, y_train,\n",
            "    validation_data=(X_val, y_val),\n",
            "    epochs=100,\n",
            "    batch_size=32,\n",
            "    callbacks=callbacks,\n",
            "    verbose=1\n",
            ")\n",
            "\n",
            "# Plot Training History\n",
            "plt.figure(figsize=(12, 5))\n",
            "plt.plot(history.history['loss'], label='Train Loss (MSE)')\n",
            "plt.plot(history.history['val_loss'], label='Val Loss (MSE)')\n",
            "plt.title('Model Training History')\n",
            "plt.xlabel('Epochs')\n",
            "plt.ylabel('Loss (MSE)')\n",
            "plt.legend()\n",
            "plt.grid(True)\n",
            "plt.show()\n"
        ]
    },
    
    # Cell: Markdown - Evaluation
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Evaluation and Visualization\n",
            "\n",
            "We evaluate the model on the **Test Set** and visualize the predictions.\n"
        ]
    },
    
    # Cell: Code - Evaluation
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ============================================\n",
            "# EVALUATE ON TEST SET\n",
            "# ============================================\n",
            "\n",
            "# Predict\n",
            "y_pred = model.predict(X_test).flatten()\n",
            "\n",
            "# Metrics\n",
            "rmse = np.sqrt(mean_squared_error(y_test, y_pred))\n",
            "mae = mean_absolute_error(y_test, y_pred)\n",
            "r2 = r2_score(y_test, y_pred)\n",
            "\n",
            "print(f\"\\nTest Set Performance:\")\n",
            "print(f\"  RMSE: {rmse:.2f}%\")\n",
            "print(f\"  MAE:  {mae:.2f}%\")\n",
            "print(f\"  R²:   {r2:.4f}\")\n",
            "\n",
            "# Visualization: Actual vs Predicted\n",
            "plt.figure(figsize=(16, 6))\n",
            "plt.plot(y_test, label='Actual RUL', color='blue', linewidth=2)\n",
            "plt.plot(y_pred, label='Predicted RUL (LSTM)', color='red', linestyle='--', linewidth=2)\n",
            "plt.title(f'LSTM RUL Prediction (Test Set) - RMSE: {rmse:.2f}%', fontsize=14)\n",
            "plt.xlabel('Time Steps (Test Set)')\n",
            "plt.ylabel('RUL (%)')\n",
            "plt.legend()\n",
            "plt.grid(True, alpha=0.3)\n",
            "plt.show()\n",
            "\n",
            "# Visualization: Error Distribution\n",
            "errors = y_test - y_pred\n",
            "plt.figure(figsize=(10, 5))\n",
            "sns.histplot(errors, kde=True, color='purple')\n",
            "plt.title('Prediction Error Distribution')\n",
            "plt.xlabel('Error (Actual - Predicted)')\n",
            "plt.grid(True, alpha=0.3)\n",
            "plt.show()\n"
        ]
    }
]

nb['cells'].extend(new_cells)

with open('notebooks/03_NASA_DL_LSTM_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("Added training and evaluation cells.")
