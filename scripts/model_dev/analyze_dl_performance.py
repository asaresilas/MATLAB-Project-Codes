"""
Analyze the DL notebook to understand the current setup and suggest improvements
"""
import json

notebook_path = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("=== CURRENT SETUP ANALYSIS ===\n")

# Check model architecture
print("1. MODEL ARCHITECTURE:")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def build_cnn_model" in source:
            print(f"Found CNN model definition in Cell {i}")
            # Count layers
            if "Conv1D(filters=64" in source:
                print("  - First Conv1D: 64 filters")
            if "Conv1D(filters=128" in source:
                print("  - Second Conv1D: 128 filters")
            if "GlobalAveragePooling1D" in source:
                print("  - Using GlobalAveragePooling1D (good!)")
            if "Dense(100" in source:
                print("  - Dense layer: 100 units")
            if "Dropout(0.5)" in source:
                print("  - Dropout: 0.5")

# Check training parameters
print("\n2. TRAINING PARAMETERS:")
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "epochs=" in source and "batch_size=" in source:
            if "epochs=20" in source:
                print("  - Epochs: 20")
            if "batch_size=32" in source:
                print("  - Batch size: 32")
            if "validation_split=0.2" in source:
                print("  - Validation split: 0.2")

# Check data
print("\n3. DATA:")
print("  - Classes: 7 (0-6)")
print("  - Sequence length: 5000 (downsampled from 100k)")
print("  - Channels: 2")

print("\n=== RECOMMENDATIONS ===\n")
print("For 60% accuracy on 7-class problem, try:")
print("1. Increase model capacity (more filters, deeper network)")
print("2. Train for more epochs (20 might be too few)")
print("3. Reduce dropout (0.5 is aggressive)")
print("4. Add data augmentation")
print("5. Check class balance (some classes might be underrepresented)")
