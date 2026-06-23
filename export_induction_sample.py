import numpy as np
import pandas as pd
import os

print("🚀 RUNNING EXTRACTION SCRIPT VERSION 2.1 (Force-Extract)")

file_path = r"D:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\datasets\Induction_Motor\x1z\x1.np"
output_path = r"D:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\results\induction_motor_x1_sample.csv"

try:
    # 1. Open the file as a raw binary stream
    print(f"🔄 Reading raw binary: {os.path.basename(file_path)}")
    
    # Each row is 200,000 samples. We want 50 rows.
    # Total samples to read = 50 * 200,000 = 10,000,000
    rows_to_get = 50
    samples_per_row = 200000
    total_to_read = rows_to_get * samples_per_row
    
    # Read only the first chunk of the file
    # We use count to stop after the first 50 rows
    data_1d = np.fromfile(file_path, dtype=np.float64, count=total_to_read)
    
    if len(data_1d) < total_to_read:
        print(f"⚠️ Warning: Only found {len(data_1d)} samples. File might be smaller than expected.")
        rows_to_get = len(data_1d) // samples_per_row
        data_1d = data_1d[:rows_to_get * samples_per_row]

    print(f"📊 Reshaping into ({rows_to_get}, {samples_per_row})...")
    subset = data_1d.reshape(rows_to_get, samples_per_row)
    
    print(f"💾 Saving to CSV...")
    df = pd.DataFrame(subset.astype(np.float32))
    df.to_csv(output_path, index_label="Trial_Row")
    
    print(f"🎉 SUCCESS! First 50 rows saved at: {output_path}")

except Exception as e:
    print(f"❌ SCRIPT ERROR: {e}")
