"""
Quick script to explore NASA dataset structure
"""
import os
import pandas as pd
import numpy as np

# Check first test folder
test1_path = 'NASA_Data/1st_test'
files = sorted(os.listdir(test1_path))[:5]

print("First 5 files in 1st_test:")
for f in files:
    print(f"  {f}")

# Load and inspect first file
if files:
    first_file = os.path.join(test1_path, files[0])
    print(f"\nLoading: {files[0]}")
    
    # NASA data is tab-separated, no header
    df = pd.read_csv(first_file, sep='\t', header=None)
    
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.shape[1]} (typically 4 bearings)")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nData statistics:")
    print(df.describe())
