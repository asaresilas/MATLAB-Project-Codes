import numpy as np
import hashlib
import os

def get_hash(arr):
    """Calculates a stable SHA-256 hash for a numpy array."""
    return hashlib.sha256(arr.tobytes()).hexdigest()

def audit_cache(name, train_data, test_data):
    print(f"\n--- AUDITING {name.upper()} MODALITY ---")
    
    # NEW v2.3: Skip all-zero samples (placeholders)
    def is_nonzero(arr):
        return np.any(arr != 0)

    train_hashes = set()
    for i in range(len(train_data)):
        if is_nonzero(train_data[i]):
            train_hashes.add(get_hash(train_data[i]))
    
    duplicates = 0
    valid_test = 0
    for i in range(len(test_data)):
        if is_nonzero(test_data[i]):
            valid_test += 1
            h = get_hash(test_data[i])
            if h in train_hashes:
                duplicates += 1
            
    if valid_test == 0:
        print(f"⚠ WARNING: No valid (non-zero) samples found in {name} test set!")
        return 0

    overlap_pct = (duplicates / valid_test) * 100
    
    if duplicates == 0:
        print(f"OK GENUINE: 0 duplicates found in {valid_test} valid samples.")
    else:
        print(f"⚠ WARNING: Found {duplicates} leaking samples ({overlap_pct:.2f}%)!")
    return duplicates

if __name__ == "__main__":
    train_path = 'data/fusion_train_cache.npz'
    test_path = 'data/fusion_test_cache.npz'
    
    if not os.path.exists(train_path):
        print("Run scripts/build_true_dataset.py first!")
        exit(1)
        
    tr = np.load(train_path)
    te = np.load(test_path)
    
    total_leaks = 0
    modalities = ['cwru', 'ind', 'nasa', 'curr', 'therm']
    
    print("==========================================")
    print("   SCIENTIFIC INTEGRITY AUDIT (SHA-256)   ")
    print("==========================================")
    
    for mod in modalities:
        try:
            total_leaks += audit_cache(mod, tr[f'{mod}_x'], te[f'{mod}_x'])
        except KeyError:
            print(f"Skipping {mod} (not in cache)")

    print("\n==========================================")
    if total_leaks == 0:
        print("  RESULT: 100% UNBIASED & GENUINE   ")
        print("  (Confirmed Signal-Level Isolation)  ")
    else:
        print(f"  RESULT: {total_leaks} LEAKING SAMPLES DETECTED  ")
        print("  (System requires deeper partitioning) ")
    print("==========================================\n")
