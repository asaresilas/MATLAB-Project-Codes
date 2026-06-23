import json
import os
import shutil

files_to_check = [
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb",
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training_fixed.ipynb",
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb",
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training_fixed.ipynb"
]

def check_file(path):
    if not os.path.exists(path):
        return False, "File not found"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "DATA BALANCE ANALYSIS" in content:
                return True, "Found fix"
            else:
                return False, "Fix NOT found"
    except Exception as e:
        return False, str(e)

print("--- Verification ---")
fixed_ml_good = False
fixed_dl_good = False

for f in files_to_check:
    status, msg = check_file(f)
    print(f"{os.path.basename(f)}: {msg}")
    if "ML_training_fixed" in f and status: fixed_ml_good = True
    if "DL_training_fixed" in f and status: fixed_dl_good = True

print("\n--- Applying Fixes & Cleanup ---")
base_dir = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks"

# 1. Overwrite ML if fixed version is good
if fixed_ml_good:
    src = os.path.join(base_dir, "06_Induction_Motor_ML_training_fixed.ipynb")
    dst = os.path.join(base_dir, "06_Induction_Motor_ML_training.ipynb")
    shutil.copy2(src, dst)
    print(f"Overwrote ML notebook with fixed version.")
else:
    print("Skipping ML overwrite - fixed version not verified.")

# 2. Overwrite DL if fixed version is good
if fixed_dl_good:
    src = os.path.join(base_dir, "06_Induction_Motor_DL_training_fixed.ipynb")
    dst = os.path.join(base_dir, "06_Induction_Motor_DL_training.ipynb")
    shutil.copy2(src, dst)
    print(f"Overwrote DL notebook with fixed version.")
else:
    print("Skipping DL overwrite - fixed version not verified.")

# 3. Delete temp files
files_to_delete = [
    "06_Induction_Motor_ML_training_fixed.ipynb",
    "06_Induction_Motor_ML_training_backup.ipynb",
    "06_Induction_Motor_DL_training_fixed.ipynb"
]

for fname in files_to_delete:
    path = os.path.join(base_dir, fname)
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted {fname}")
    else:
        print(f"File {fname} not found (already deleted?)")
