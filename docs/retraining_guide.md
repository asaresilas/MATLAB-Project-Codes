# Guide: Retraining the NASA RUL Model

This guide explains how to retrain the Bi-LSTM model if you have new bearing failure data or want to experiment with different architectures.

## When to Retrain

You should retrain the model when:
- ✓ You have new bearing failure data from your motors
- ✓ The current predictions are consistently inaccurate
- ✓ You want to try different model architectures (1D-CNN, CNN-LSTM, etc.)
- ✓ You want to tune hyperparameters for better performance

## Prerequisites

Ensure you have the required packages:
```bash
pip install tensorflow scikit-learn pandas numpy matplotlib seaborn
```

## Step 1: Prepare Your Data

The model expects data in the NASA IMS bearing dataset format:

### Data Structure
```
data/
└── nasa_ims/
    ├── 1st_test/
    │   ├── 2004.02.12.10.32.39  # Timestamp file
    │   ├── 2004.02.12.10.42.39
    │   └── ...
    └── 2nd_test/
        └── ...
```

### File Format
Each file contains 4 columns (one per bearing), 20,480 rows (vibration readings):
```
0.123  0.145  0.098  0.112
0.125  0.143  0.099  0.110
...
```

### If You Have Custom Data
If your data is in a different format, you'll need to:

1. **Convert to NASA format**, OR
2. **Modify the data loader** in `notebooks/02_NASA_DL_training.ipynb`

Example conversion script:
```python
import pandas as pd
import numpy as np

# Your custom data
your_data = pd.read_csv('your_bearing_data.csv')

# Convert to NASA format (4 bearings × 20480 samples)
# Adjust based on your data structure
nasa_format = your_data.values.reshape(-1, 20480, 4)

# Save each time window as a separate file
for i, window in enumerate(nasa_format):
    filename = f"data/custom_test/timestamp_{i:04d}"
    np.savetxt(filename, window, fmt='%.6f')
```

## Step 2: Open the Training Notebook

Navigate to and open:
```
notebooks/02_NASA_DL_training.ipynb
```

## Step 3: Configure Training Parameters

In the notebook, locate the configuration cell and adjust:

```python
# Model Selection
MODEL_TYPE = 'Bi-LSTM'  # Options: 'Bi-LSTM', '1D-CNN', 'CNN-LSTM', 'Bi-LSTM-Attn'

# Hyperparameters
WINDOW_SIZE = 10        # Number of timesteps in sequence
BATCH_SIZE = 32         # Training batch size
EPOCHS = 100            # Number of training epochs
LEARNING_RATE = 0.001   # Adam optimizer learning rate

# Data Split
TEST_SIZE = 0.2         # 20% for testing
VALIDATION_SPLIT = 0.2  # 20% of training for validation

# Feature Extraction
FEATURES_PER_BEARING = 9  # Don't change unless modifying extract_features()
```

## Step 4: Run the Notebook

Execute all cells in order:

1. **Data Loading** - Loads bearing data files
2. **Feature Extraction** - Extracts 9 features per bearing
3. **RUL Labeling** - Assigns RUL values based on time-to-failure
4. **Sequence Creation** - Creates windowed sequences
5. **Data Scaling** - Normalizes features
6. **Model Building** - Constructs the neural network
7. **Training** - Trains the model
8. **Evaluation** - Tests on holdout data
9. **Model Saving** - Saves model and scaler

### Expected Output
```
Epoch 1/100
Loss: 245.32 - Val Loss: 198.45
...
Epoch 100/100
Loss: 12.34 - Val Loss: 15.67

Test Results:
RMSE: 18.5 hours
MAE: 12.3 hours
R²: 0.89

✓ Model saved to: Trained_models/nasa_dl_comparison/Bi-LSTM/
```

## Step 5: Verify the New Model

After training, the notebook saves:
- `Bi-LSTM_model.keras` - The trained model
- `Bi-LSTM_scaler.pkl` - Feature scaler
- `Bi-LSTM_metadata.json` - Training metadata

Run the comparison test to verify:
```bash
python tests/test_rul_comparison.py
```

## Step 6: Deploy the New Model

The system automatically loads the latest model from `Trained_models/nasa_dl_comparison/Bi-LSTM/`. No code changes needed!

Just restart your application:
```bash
# For MATLAB interface
# Simply restart MATLAB and call analyze_motor_data()

# For API
cd backend
uvicorn app.main:app --reload
```

## Trying Different Model Architectures

The notebook includes 4 pre-configured architectures:

### 1. Bi-LSTM (Current)
- Best for: Sequential patterns, temporal dependencies
- Pros: Captures long-term trends
- Cons: Slower training

### 2. 1D-CNN
- Best for: Local patterns, feature extraction
- Pros: Fast training, good for stationary signals
- Cons: May miss long-term dependencies

### 3. CNN-LSTM
- Best for: Hybrid approach
- Pros: Combines CNN feature extraction with LSTM temporal modeling
- Cons: More complex, requires more data

### 4. Bi-LSTM-Attn (Attention)
- Best for: Focusing on important time windows
- Pros: Can identify critical degradation periods
- Cons: Most complex, slowest training

To try a different architecture:
```python
# In the notebook, change:
MODEL_TYPE = '1D-CNN'  # or 'CNN-LSTM', 'Bi-LSTM-Attn'

# Then run all cells
```

## Performance Comparison

After training multiple models, compare them:

```python
import json
import pandas as pd

models = ['Bi-LSTM', '1D-CNN', 'CNN-LSTM', 'Bi-LSTM-Attn']
results = []

for model in models:
    with open(f'Trained_models/nasa_dl_comparison/{model}/{model}_metadata.json') as f:
        metadata = json.load(f)
        results.append({
            'Model': model,
            'RMSE': metadata['test_rmse'],
            'MAE': metadata['test_mae'],
            'R²': metadata['test_r2']
        })

df = pd.DataFrame(results)
print(df.to_string(index=False))

# Choose the model with lowest RMSE and highest R²
```

## Troubleshooting

### Issue: "Out of Memory" Error
**Solution:** Reduce `BATCH_SIZE` or `WINDOW_SIZE`
```python
BATCH_SIZE = 16  # Instead of 32
WINDOW_SIZE = 5  # Instead of 10
```

### Issue: Model Overfitting (Train loss << Val loss)
**Solution:** Add regularization or reduce model complexity
```python
# In model definition, add dropout:
model.add(Dropout(0.3))

# Or reduce LSTM units:
LSTM(units=32)  # Instead of 64
```

### Issue: Poor Predictions
**Solution:** 
1. Check if data is properly normalized
2. Increase `EPOCHS`
3. Try different `LEARNING_RATE`
4. Ensure RUL labels are correct

### Issue: Training Too Slow
**Solution:**
1. Use GPU if available
2. Reduce `WINDOW_SIZE`
3. Try simpler model (1D-CNN instead of Bi-LSTM)

## Best Practices

1. **Always keep a backup** of the working model before retraining
2. **Use validation data** to prevent overfitting
3. **Document your changes** in the metadata file
4. **Test thoroughly** with `test_rul_comparison.py` before deployment
5. **Monitor performance** over time and retrain periodically

## Next Steps

After successful retraining:
- ✓ Run comparison tests
- ✓ Update documentation with new performance metrics
- ✓ Deploy to production
- ✓ Monitor real-world performance
- ✓ Collect feedback for next iteration
