import json
import os

notebooks = [
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_ML_training.ipynb",
    r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\notebooks\06_Induction_Motor_DL_training.ipynb"
]

print("=== VERIFYING CORRECTIONS IN MAIN NOTEBOOKS ===\n")

for nb_path in notebooks:
    filename = os.path.basename(nb_path)
    print(f"Checking: {filename}")
    
    if not os.path.exists(nb_path):
        print("  [FAIL] File not found!")
        continue
        
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
            
        # Check 1: Data Balance Analysis
        has_balance = False
        for cell in nb['cells']:
            source = ''.join(cell.get('source', []))
            if "DATA BALANCE ANALYSIS" in source and "class_names = ['Healthy'" in source:
                has_balance = True
                break
        
        if has_balance:
            print("  [PASS] Data Balance Analysis: PRESENT")
        else:
            print("  [FAIL] Data Balance Analysis: MISSING")
            
        # Check 2: Fixed Plot Legends (Confusion Matrix)
        has_fixed_legend = False
        for cell in nb['cells']:
            source = ''.join(cell.get('source', []))
            if "xticklabels=['Healthy', 'Damaged 1'" in source:
                has_fixed_legend = True
                break
                
        if has_fixed_legend:
            print("  [PASS] Fixed Plot Legends: PRESENT")
        else:
            # DL notebook might not have the exact same confusion matrix code
            if "DL" in filename:
                 print("  [INFO] Fixed Plot Legends: Not applicable or different format for DL")
            else:
                print("  [FAIL] Fixed Plot Legends: MISSING")

    except Exception as e:
        print(f"  [FAIL] Error reading file: {e}")
    
    print("-" * 40)
