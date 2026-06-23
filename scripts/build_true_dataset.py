import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import glob
import numpy as np
import pandas as pd
import scipy.io
import hashlib
import math
from tqdm import tqdm

from src.data.current_signature_loader import CurrentSignatureLoader

np.random.seed(42)

def balanced_split_resample(classes_of_signals, train_n=500, test_n=200, default_shape=None, window_size=1000, stride=250):
    """Partition ORIGINAL SIGNALS into train/test before augmentation for 100% isolation."""
    # Source Level Deduplication (New in v2.3)
    def is_duplicate(sig1, sig_list):
        if not sig_list: return False
        h1 = hashlib.md5(sig1[:1000].tobytes()).hexdigest()
        for s in sig_list:
            if math.isclose(np.mean(sig1), np.mean(s), rel_tol=1e-5):
                if h1 == hashlib.md5(s[:1000].tobytes()).hexdigest():
                    return True
        return False

    train_x, train_y = [], []
    test_x, test_y = [], []
    
    for class_idx in range(3):
        signals = classes_of_signals[class_idx]
        if not signals:
            raise ValueError(f"CRITICAL ERROR: No signals found for Class {class_idx}. Dataset loading failed!")
            
        np.random.shuffle(signals)
        # Unique Source Filtering
        unique_signals = []
        for s in signals:
            if not is_duplicate(s, unique_signals):
                unique_signals.append(s)
        
        split_idx = max(1, int(len(unique_signals) * 0.70))
        train_pool = unique_signals[:split_idx]
        test_pool = unique_signals[split_idx:]
        
        if not test_pool and len(unique_signals) > 0:
             pass # Removed leakage fallback. If 1 signal exists, it stays in train only.
            
        # Case A: Sliding Window Augmentation (Signals)
        if window_size > 0:
            for pool, target_list, target_n in [(train_pool, train_x, train_n), (test_pool, test_x, test_n)]:
                while len(target_list) < (class_idx + 1) * target_n:
                    sig = pool[np.random.randint(len(pool))]
                    # Windowing
                    added = False
                    for start in range(0, len(sig) - window_size, stride):
                        if len(target_list) >= (class_idx + 1) * target_n: break
                        target_list.append(sig[start:start + window_size].astype(np.float32))
                        train_y.append(class_idx) if target_list is train_x else test_y.append(class_idx)
                        added = True
                    if not added: # Fallback for short signals
                        pad_sig = np.zeros((window_size, sig.shape[1] if len(sig.shape)>1 else 1), dtype=np.float32)
                        pad_sig[:min(len(sig), window_size)] = sig[:min(len(sig), window_size)]
                        target_list.append(pad_sig)
                        train_y.append(class_idx) if target_list is train_x else test_y.append(class_idx)
        
        # Case B: Direct Sampling (Images/Pre-processed Features)
        else:
            for pool, target_list, target_n in [(train_pool, train_x, train_n), (test_pool, test_x, test_n)]:
                while len(target_list) < (class_idx + 1) * target_n:
                    img = pool[np.random.randint(len(pool))]
                    target_list.append(img)
                    train_y.append(class_idx) if target_list is train_x else test_y.append(class_idx)
            
    return (train_x, train_y), (test_x, test_y)

def extract_nasa_features(signal):
    return [
        np.sqrt(np.mean(signal ** 2)),
        np.mean(signal),
        np.std(signal),
        np.max(signal),
        np.min(signal),
        0.0 if np.std(signal) == 0 else np.mean((signal - np.mean(signal)) ** 4) / (np.std(signal) ** 4),
        0.0 if np.std(signal) == 0 else np.mean((signal - np.mean(signal)) ** 3) / (np.std(signal) ** 3),
        np.max(signal) - np.min(signal),
        np.max(np.abs(signal)) / (np.sqrt(np.mean(signal ** 2)) + 1e-9),
    ]

def get_base_nasa_features(file_path, bearing_idx):
    try:
        df = pd.read_csv(file_path, sep="\t", header=None).values
        if df.shape[1] > bearing_idx:
            return extract_nasa_features(df[:, bearing_idx])
        return [0] * 9
    except Exception:
        return [0] * 9

def fast_nasa_build(train_n=105, test_n=45):
    nasa_dir = os.path.join("datasets", "NASA", "1st_test", "1st_test")
    
    train_x, train_y, train_rul = [], [], []
    test_x, test_y, test_rul = [], [], []
    
    if os.path.exists(nasa_dir):
        files = sorted(glob.glob(os.path.join(nasa_dir, "*")))
        
        split_idx = int(len(files[:1000]) * 0.7)
        train_files = files[:split_idx]
        test_files = files[split_idx:1000]
        
        def process_files(file_list, target_x, target_y, target_rul, max_n):
            features = []
            print(f"Extracting NASA features for {len(file_list)} files...")
            for file_path in tqdm(file_list):
                row_feats = []
                for bearing_idx in range(4):
                    row_feats.extend(get_base_nasa_features(file_path, bearing_idx))
                features.append(np.array(row_feats, dtype=np.float32))
            
            features = np.array(features)
            if len(features) < 30: return
            
            counts = {0: 0, 1: 0, 2: 0}
            for i in range(len(features) - 30):
                seq = features[i:i + 30, :]
                rul = 1.0 - (i / float(len(features)))
                c_idx = 0 if rul > 0.6 else (1 if rul > 0.2 else 2)
                
                if counts[c_idx] < max_n:
                    target_x.append(seq)
                    target_y.append(c_idx)
                    target_rul.append(rul * 100.0)
                    counts[c_idx] += 1

        process_files(train_files, train_x, train_y, train_rul, train_n)
        process_files(test_files, test_x, test_y, test_rul, test_n)

    return (train_x, train_y, train_rul), (test_x, test_y, test_rul)

def fast_cwru_build(train_n=500, test_n=200):
    cwru_dir = os.path.join("datasets", "CWRU")
    files_map = {0: ["97.mat", "98.mat", "99.mat", "100.mat"], 
                 1: ["105.mat", "118.mat", "169.mat", "185.mat", "209.mat"],
                 2: ["130.mat", "144.mat", "156.mat", "197.mat", "222.mat"]}
    classes = [[], [], []]
    for c_idx, files in files_map.items():
        for f in files:
            p = os.path.join(cwru_dir, f)
            if os.path.exists(p):
                mat = scipy.io.loadmat(p)
                for k, v in mat.items():
                    if "DE_time" in k: classes[c_idx].append(v.flatten().reshape(-1, 1))
    return balanced_split_resample(classes, train_n, test_n, (1000, 1), window_size=1000, stride=250)

def fast_induction_build(train_n=500, test_n=200):
    ind_dir = os.path.join("datasets", "Induction_Motor")
    classes = [[], [], []]
    if os.path.exists(ind_dir):
        import h5py
        struct_map = {
            'struct_rs_R1.mat': 0, 
            'struct_r1b_R1.mat': 1, 
            'struct_r2b_R1.mat': 2,
            'struct_r3b_R1.mat': 2,
            'struct_r4b_R1.mat': 2
        }
        for filename, c_idx in struct_map.items():
            p = os.path.join(ind_dir, filename)
            if os.path.exists(p):
                try:
                    with h5py.File(p, 'r') as f:
                        # Recursive Deep-Scan with Reference Dereferencing
                        def find_signal(obj):
                            if isinstance(obj, h5py.Dataset):
                                data = obj[:]
                                # If it's a dataset of references (Cell Array), dereference it
                                if data.dtype == object:
                                    for ref in data.flatten():
                                        try: return f[ref][:]
                                        except: continue
                                return data
                            if isinstance(obj, (h5py.Group, h5py.File)):
                                for k in sorted(obj.keys(), key=lambda x: x.lower() not in ['ia', 'accel', 'vibr']):
                                    if k.startswith('#'): continue
                                    res = find_signal(obj[k])
                                    if res is not None: return res
                            return None
                            
                        raw_data = find_signal(f)
                        
                        if raw_data is not None:
                            if raw_data.shape[0] < raw_data.shape[1]: raw_data = raw_data.T
                            
                            # Segmentation: Partition the massive signal into 20 sub-signals
                            # to provide enough variety for the train/test split
                            n_chunks = 20
                            chunk_len = len(raw_data) // n_chunks
                            for i in range(n_chunks):
                                segment = raw_data[i*chunk_len : (i+1)*chunk_len]
                                if len(segment) >= 2048:
                                    classes[c_idx].append(segment.astype(np.float32))
                        else:
                            print(f"Warning: No signal found in {filename}")
                except Exception as exc:
                    print(f"Error loading {filename}: {exc}")
    return balanced_split_resample(classes, train_n, test_n, (2048, 1), window_size=2048, stride=400)

def fast_current_build(train_n=500, test_n=200):
    current_dir = os.path.join("datasets", "Current_Signature", "Current Signature Dataset of Three-Phase Induction Motor under Varying Load Conditions")
    classes = [[], [], []]
    if os.path.exists(current_dir):
        try:
            loader = CurrentSignatureLoader(current_dir)
            # Assuming loader gives access to raw full signals or minimally windowed ones
            X_raw, y_raw = loader.load_raw_data()
            label_map = {"healthy": 0, "bearing_fault": 1, "broken_rotor_bar": 2}
            for sample, label in zip(X_raw, y_raw):
                class_idx = label_map.get(label)
                if class_idx is not None:
                    classes[class_idx].append(sample.astype(np.float32))
        except Exception as exc: print(f"Current error: {exc}")
    return balanced_split_resample(classes, train_n, test_n, (1000, 3), window_size=1000, stride=250)

def fast_thermal_build(train_n=105, test_n=45):
    thermal_dir = os.path.join("datasets", "Thermal", "test")
    classes = [[], [], []]
    
    if os.path.exists(thermal_dir):
        from PIL import Image
        normal_dirs = ["Noload"]
        warning_dirs = ["A10", "Fan", "Rotor-0"]
        critical_dirs = ["A30", "A50", "A_B50", "A_C30", "A_C_B30"]

        for class_idx, dir_names in enumerate([normal_dirs, warning_dirs, critical_dirs]):
            for dir_name in dir_names:
                path = os.path.join(thermal_dir, dir_name)
                if not os.path.exists(path): continue
                images = []
                for pattern in ("*.png", "*.jpg", "*.jpeg", "*.bmp"):
                    images.extend(glob.glob(os.path.join(path, pattern)))
                for image_path in images[:30]:
                    try:
                        img = Image.open(image_path).convert("RGB").resize((224, 224))
                        classes[class_idx].append(np.array(img, dtype=np.uint8))
                    except Exception: pass

    return balanced_split_resample(classes, train_n, test_n, (224, 224, 3), window_size=0)

print("Building TRUE Benchmark Validation Caches (Leakage-Free Splitting)...")
# Ensure absolute path to the project data directory
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

tr_n, te_n = 500, 200  # Increased for Meta-DL Stability (Total 2,100 samples)
print("1/5 CWRU (Augmented Sliding Window)...")
cwru_tr, cwru_te = fast_cwru_build(tr_n, te_n)
print("2/5 Induction...")
ind_tr, ind_te = fast_induction_build(tr_n, te_n)
print("3/5 NASA...")
nasa_tr, nasa_te = fast_nasa_build(tr_n, te_n)
print("4/5 Current...")
curr_tr, curr_te = fast_current_build(tr_n, te_n)
print("5/5 Thermal...")
therm_tr, therm_te = fast_thermal_build(tr_n, te_n)

# Save caches with absolute paths
train_path = os.path.join(DATA_DIR, "fusion_train_cache.npz")
test_path = os.path.join(DATA_DIR, "fusion_test_cache.npz")

np.savez_compressed(
    train_path,
    cwru_x=np.array(cwru_tr[0], dtype=np.float32), cwru_y=np.array(cwru_tr[1], dtype=np.int32),
    ind_x=np.array(ind_tr[0], dtype=np.float32), ind_y=np.array(ind_tr[1], dtype=np.int32),
    nasa_x=np.array(nasa_tr[0], dtype=np.float32), nasa_y=np.array(nasa_tr[1], dtype=np.int32),
    nasa_rul=np.array(nasa_tr[2], dtype=np.float32),
    curr_x=np.array(curr_tr[0], dtype=np.float32), curr_y=np.array(curr_tr[1], dtype=np.int32),
    therm_x=np.array(therm_tr[0], dtype=np.uint8), therm_y=np.array(therm_tr[1], dtype=np.int32),
)

np.savez_compressed(
    test_path,
    cwru_x=np.array(cwru_te[0], dtype=np.float32), cwru_y=np.array(cwru_te[1], dtype=np.int32),
    ind_x=np.array(ind_te[0], dtype=np.float32), ind_y=np.array(ind_te[1], dtype=np.int32),
    nasa_x=np.array(nasa_te[0], dtype=np.float32), nasa_y=np.array(nasa_te[1], dtype=np.int32),
    nasa_rul=np.array(nasa_te[2], dtype=np.float32),
    curr_x=np.array(curr_te[0], dtype=np.float32), curr_y=np.array(curr_te[1], dtype=np.int32),
    therm_x=np.array(therm_te[0], dtype=np.uint8), therm_y=np.array(therm_te[1], dtype=np.int32),
)

print(f"\nOK SUCCESS: Augmented samples saved to:\n  {train_path}\n  {test_path}")
