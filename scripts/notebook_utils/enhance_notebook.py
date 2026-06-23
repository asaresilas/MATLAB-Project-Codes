"""
Script to enhance the CNN training notebook with detailed markdown and code comments
"""
import json
import copy

# Load the original notebook
with open('notebooks/01_DL_cnn_training.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Enhanced markdown content for each section
enhanced_markdown = {
    0: [
        "# Deep Learning Model Training - 1D CNN\n",
        "\n",
        "This notebook demonstrates training a **1D Convolutional Neural Network (CNN)** for bearing fault diagnosis.\n",
        "\n",
        "## Key Differences: Traditional ML vs Deep Learning\n",
        "\n",
        "| Aspect | Traditional ML (RF, SVM, GB) | Deep Learning (CNN) |\n",
        "|--------|------------------------------|---------------------|\n",
        "| **Input** | Manually extracted features (RMS, mean, std, kurtosis, etc.) | Raw vibration signals |\n",
        "| **Feature Engineering** | Manual - requires domain expertise | Automatic - network learns features |\n",
        "| **Data Requirements** | Works with smaller datasets | Requires larger datasets |\n",
        "| **Interpretability** | High - can see which features matter | Lower - \"black box\" |\n",
        "| **Performance** | Good for simple patterns | Better for complex patterns |\n",
        "\n",
        "## Why Use CNN for Vibration Analysis?\n",
        "\n",
        "1. **Automatic Feature Learning**: CNNs learn optimal features directly from raw signals\n",
        "2. **Spatial Patterns**: Can detect local patterns in time-series data\n",
        "3. **Translation Invariance**: Fault patterns detected regardless of position in signal\n",
        "4. **Hierarchical Features**: Learns simple patterns first, then complex combinations\n"
    ],
    
    2: [
        "## 1. Load Raw Signal Data\n",
        "\n",
        "Unlike traditional ML, we work with **raw vibration signals** instead of extracted features.\n",
        "\n",
        "### Data Processing Steps:\n",
        "1. Load .mat files from CWRU dataset\n",
        "2. Split long signals into fixed-length chunks (1000 samples each)\n",
        "3. Create labels for each chunk\n",
        "\n",
        "### Why 1000 samples?\n",
        "- Balances between:\n",
        "  - **Too short**: May miss fault patterns\n",
        "  - **Too long**: Requires more memory, slower training\n",
        "- At 12kHz sampling rate: 1000 samples ≈ 83ms of data\n"
    ],
    
    4: [
        "## 2. Data Normalization\n",
        "\n",
        "### Why Normalize?\n",
        "Neural networks train better when inputs are on similar scales.\n",
        "\n",
        "### Normalization Method:\n",
        "**Per-sample Z-score normalization**:\n",
        "```\n",
        "normalized_signal = (signal - mean) / std\n",
        "```\n",
        "\n",
        "### Benefits:\n",
        "- Removes amplitude variations between different sensors/conditions\n",
        "- Focuses on signal **shape** rather than absolute values\n",
        "- Helps gradient descent converge faster\n",
        "- Prevents large values from dominating the learning\n"
    ],
    
    6: [
        "## 3. Class Distribution & Balancing\n",
        "\n",
        "### The Imbalance Problem:\n",
        "Real-world datasets often have:\n",
        "- **Many normal samples** (machine runs normally most of the time)\n",
        "- **Few fault samples** (faults are rare)\n",
        "\n",
        "### Why This Matters:\n",
        "- Model may learn to always predict \"Normal\" (high accuracy but useless!)\n",
        "- Rare faults won't be detected\n",
        "\n",
        "### Solution: SMOTE (Synthetic Minority Over-sampling Technique)\n",
        "- Creates synthetic samples for minority classes\n",
        "- Interpolates between existing samples\n",
        "- Results in balanced dataset for training\n",
        "\n",
        "### Note:\n",
        "We only balance the **training set**, not validation/test sets (they should reflect real distribution)\n"
    ],
    
    9: [
        "## 4. Train-Validation-Test Split\n",
        "\n",
        "### Three-Way Split Strategy:\n",
        "\n",
        "```\n",
        "Original Data (100%)\n",
        "    |\n",
        "    ├── Training Set (60%)   ← Used to train the model\n",
        "    ├── Validation Set (20%) ← Used to tune hyperparameters & monitor overfitting\n",
        "    └── Test Set (20%)       ← Final evaluation (NEVER seen during training)\n",
        "```\n",
        "\n",
        "### Why This Split?\n",
        "- **Training**: Model learns patterns\n",
        "- **Validation**: Check if model generalizes (not just memorizing)\n",
        "- **Test**: Unbiased final performance estimate\n",
        "\n",
        "### Important:\n",
        "- Stratified split ensures each set has same class distribution\n",
        "- Random state fixed for reproducibility\n"
    ],
    
    11: [
        "## 5. Build and Train 1D CNN Model\n",
        "\n",
        "### CNN Architecture:\n",
        "\n",
        "```\n",
        "Input (1000 samples)\n",
        "    ↓\n",
        "Conv1D (64 filters, kernel=3) + ReLU + MaxPool\n",
        "    ↓\n",
        "Conv1D (128 filters, kernel=3) + ReLU + MaxPool  \n",
        "    ↓\n",
        "Conv1D (128 filters, kernel=3) + ReLU + MaxPool\n",
        "    ↓\n",
        "Flatten\n",
        "    ↓\n",
        "Dense (128) + ReLU + Dropout(0.5)\n",
        "    ↓\n",
        "Dense (4) + Softmax → [Normal, Inner, Ball, Outer]\n",
        "```\n",
        "\n",
        "### Key Components:\n",
        "- **Conv1D**: Learns local patterns in signal\n",
        "- **MaxPooling**: Reduces size, provides translation invariance\n",
        "- **Dropout**: Prevents overfitting by randomly dropping neurons\n",
        "- **Softmax**: Converts outputs to probabilities\n",
        "\n",
        "### Training Strategy:\n",
        "- **Early Stopping**: Stop if validation loss doesn't improve for 10 epochs\n",
        "- **Learning Rate Reduction**: Reduce LR if stuck in plateau\n",
        "- **Batch Size**: 64 samples per update\n"
    ],
    
    14: [
        "## 6. Visualize Training History\n",
        "\n",
        "### What to Look For:\n",
        "\n",
        "**Good Training:**\n",
        "- Training & validation loss both decrease\n",
        "- Training & validation accuracy both increase\n",
        "- Curves are close together\n",
        "\n",
        "**Overfitting Signs:**\n",
        "- Training loss keeps decreasing\n",
        "- Validation loss starts increasing\n",
        "- Large gap between training and validation accuracy\n",
        "\n",
        "**Underfitting Signs:**\n",
        "- Both losses remain high\n",
        "- Accuracy plateaus at low value\n"
    ],
    
    16: [
        "## 7. Evaluate on Test Set\n",
        "\n",
        "### Evaluation Metrics:\n",
        "\n",
        "1. **Accuracy**: Overall correct predictions\n",
        "2. **Precision**: Of predicted faults, how many are real?\n",
        "3. **Recall**: Of real faults, how many did we detect?\n",
        "4. **F1-Score**: Harmonic mean of precision & recall\n",
        "5. **Confusion Matrix**: Shows which classes are confused\n",
        "\n",
        "### Why Multiple Metrics?\n",
        "- Accuracy alone can be misleading with imbalanced data\n",
        "- Precision/Recall trade-off depends on application:\n",
        "  - **High Recall**: Don't miss any faults (safety-critical)\n",
        "  - **High Precision**: Avoid false alarms (cost of inspection)\n"
    ],
    
    18: [
        "## 8. ROC Curve (Receiver Operating Characteristic)\n",
        "\n",
        "### What is ROC?\n",
        "- Plots True Positive Rate vs False Positive Rate\n",
        "- Shows model performance across all classification thresholds\n",
        "\n",
        "### AUC (Area Under Curve):\n",
        "- **AUC = 1.0**: Perfect classifier\n",
        "- **AUC = 0.9-1.0**: Excellent\n",
        "- **AUC = 0.8-0.9**: Good\n",
        "- **AUC = 0.7-0.8**: Fair\n",
        "- **AUC = 0.5**: Random guessing\n",
        "\n",
        "### Multi-class ROC:\n",
        "- One curve per class (One-vs-Rest approach)\n",
        "- Micro-average: Global performance\n",
        "- Macro-average: Average of per-class performance\n"
    ],
    
    20: [
        "## 9. Save the Model\n",
        "\n",
        "### Model Saving Format:\n",
        "\n",
        "**For Keras/TensorFlow models**: Use `.h5` or SavedModel format\n",
        "```python\n",
        "model.save('model.h5')  # HDF5 format\n",
        "```\n",
        "\n",
        "**For Scikit-learn models**: Use `.pkl` (pickle) format\n",
        "```python\n",
        "joblib.dump(model, 'model.pkl')\n",
        "```\n",
        "\n",
        "### Why .h5 for Deep Learning?\n",
        "- Stores complete model architecture\n",
        "- Saves trained weights\n",
        "- Includes optimizer state\n",
        "- Preserves training configuration\n",
        "- Can resume training later\n",
        "\n",
        "### Loading the Model:\n",
        "```python\n",
        "from tensorflow import keras\n",
        "loaded_model = keras.models.load_model('cnn_model.h5')\n",
        "```\n"
    ],
    
    22: [
        "## 10. Summary\n",
        "\n",
        "### What We Accomplished:\n",
        "\n",
        "✅ **Data Preparation**:\n",
        "- Loaded raw vibration signals from CWRU dataset\n",
        "- Normalized signals for better training\n",
        "- Balanced classes using SMOTE\n",
        "- Split into train/validation/test sets\n",
        "\n",
        "✅ **Model Training**:\n",
        "- Built 1D CNN architecture\n",
        "- Trained with early stopping and LR reduction\n",
        "- Monitored training/validation performance\n",
        "\n",
        "✅ **Evaluation**:\n",
        "- Achieved high accuracy on test set\n",
        "- Analyzed confusion matrix\n",
        "- Plotted ROC curves\n",
        "- Saved model for deployment\n",
        "\n",
        "### Next Steps:\n",
        "1. **Test on other datasets** (NASA, Induction Motor, CIA-1)\n",
        "2. **Integrate with interface.py** for real-time predictions\n",
        "3. **Add uncertainty quantification** (Monte Carlo Dropout)\n",
        "4. **Implement RUL prediction** using LSTM\n",
        "\n",
        "### Key Takeaways:\n",
        "- CNNs can learn features automatically from raw signals\n",
        "- Proper data preprocessing is crucial\n",
        "- Monitor both training and validation metrics\n",
        "- Use multiple evaluation metrics for comprehensive assessment\n"
    ]
}

# Update markdown cells
for cell_idx, new_content in enhanced_markdown.items():
    if cell_idx < len(nb['cells']) and nb['cells'][cell_idx]['cell_type'] == 'markdown':
        nb['cells'][cell_idx]['source'] = new_content

print("Enhanced markdown cells")

# Save the enhanced notebook
with open('notebooks/01_DL_cnn_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4, ensure_ascii=False)

print("✅ Successfully enhanced notebook with detailed markdown explanations!")
print(f"Total cells: {len(nb['cells'])}")
print(f"Enhanced {len(enhanced_markdown)} markdown cells")
