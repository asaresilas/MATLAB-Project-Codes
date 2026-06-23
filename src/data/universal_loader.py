"""
universal_loader.py — Legacy multi-dataset loader.

DEPRECATION NOTICE:
  This module's prepare_data() method is NOT used in the official publication
  pipeline. It has two known methodological problems:
  1. Post-merge global shuffle (lines ~292-295) destroys NASA temporal ordering,
     making RUL evaluation invalid after a random permutation mixes early and
     late bearing-life samples across train/test.
  2. Per-dataset train/test isolation is not enforced; sliding windows from the
     same file can appear in both train and test splits (leakage).

  The official pipeline is:
    scripts/build_latent_digital_twin.py  (generates aligned synthetic data)
    scripts/generate_meta_features.py     (extracts 32-dim meta-feature vectors)
    scripts/train_meta_fusion.py          (trains the meta-learner)
    scripts/generate_publication_results.py

  Use this module only for legacy exploratory analysis, not for any reported metrics.
"""

import os
import warnings
import numpy as np
import pandas as pd
import sys
from tensorflow.keras.utils import to_categorical
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.loaders import CWRULoader, NASALoader, CIA1Loader
from src.data.current_signature_loader import CurrentSignatureLoader
import base64
import io

class UniversalDataLoader:
    def __init__(self, base_dir):
        """
        Universal Data Loader for Digital Twin Predictive Maintenance.
        Integrates CWRU, NASA, CIA-1, and Current Signature datasets.
        
        Args:
            base_dir (str): Root directory containing all dataset folders.
        """
        self.base_dir = base_dir
        self.cwru_dir = os.path.join(base_dir, 'datasets', 'CWRU')
        self.nasa_dir = os.path.join(base_dir, 'datasets', 'NASA')
        self.cia1_dir = os.path.join(base_dir, 'datasets', 'CIA-1')
        self.current_dir = os.path.join(base_dir, 'datasets', 'Current_Signature', 'Current Signature Dataset of Three-Phase Induction Motor under Varying Load Conditions')
        self.thermal_dir = os.path.join(base_dir, 'datasets', 'Thermal')
        
        # Unified Severity Mapping (Aligned with Meta-Fusion Model)
        self.class_map = {
            'Healthy': 0,
            'Warning': 1,
            'Critical': 2
        }
        self.num_classes = len(self.class_map)
        
    def _pad_or_truncate(self, signal, length=2048):
        """Resizes signal to fixed length."""
        if len(signal) >= length:
            return signal[:length]
        else:
            return np.pad(signal, (0, length - len(signal)), 'constant')

    def load_cwru(self):
        """Loads CWRU data (Vibration only)."""
        print("Loading CWRU Dataset...")
        loader = CWRULoader(self.cwru_dir)
        X_vib = []
        y = []
        
        # Walk through directory to find .mat files
        for root, dirs, files in os.walk(self.cwru_dir):
            for file in files:
                if file.endswith('.mat'):
                    try:
                        signal = loader.load_file(file)
                        # Segment into windows
                        window_size = 2048
                        stride = 2048 
                        
                        if 'Normal' in file:
                            label = self.class_map['Healthy']
                        elif '007' in file: # 0.007 inch faults are early warnings
                            label = self.class_map['Warning']
                        else: # Larger faults are critical
                            label = self.class_map['Critical']

                        for i in range(0, len(signal) - window_size, stride):
                            window = signal[i:i+window_size]
                            X_vib.append(window)
                            y.append(label)
                    except Exception as e:
                        pass
                        
        X_vib = np.array(X_vib)
        if len(X_vib) > 0:
            X_vib = X_vib.reshape(-1, 2048, 1)
        
        # Other modalities
        X_curr = np.zeros((len(X_vib), 2048, 3))
        X_tab = np.zeros((len(X_vib), 9))
        
        # Targets
        y = np.array(y)
        y_rul = np.zeros(len(y)) # Not applicable
        mask_rul = np.zeros(len(y))
        y_anomaly = (y != self.class_map['Healthy']).astype(int)
        
        return X_vib, X_curr, X_tab, y, y_rul, mask_rul, y_anomaly

    def load_current_signature(self):
        """Loads Current Signature data (Current only)."""
        print("Loading Current Signature Dataset...")
        loader = CurrentSignatureLoader(self.current_dir)
        X_curr_raw, y_raw = loader.load_raw_data(window_size=2048, stride=2048)
        
        y = []
        for label in y_raw:
            if label == 'healthy':
                y.append(self.class_map['Healthy'])
            elif label == 'bearing_fault':
                y.append(self.class_map['Warning']) # Early stage
            elif label == 'broken_rotor_bar':
                y.append(self.class_map['Critical']) # Late stage
            else:
                y.append(-1)
        
        y = np.array(y)
        
        X_vib = np.zeros((len(X_curr_raw), 2048, 1))
        X_tab = np.zeros((len(X_curr_raw), 9))
        
        y_rul = np.zeros(len(y))
        mask_rul = np.zeros(len(y))
        y_anomaly = (y != self.class_map['Healthy']).astype(int)
        
        return X_vib, X_curr_raw, X_tab, y, y_rul, mask_rul, y_anomaly

    def load_cia1(self):
        """Loads CIA-1 data (Tabular only)."""
        print("Loading CIA-1 Dataset...")
        loader = CIA1Loader(self.cia1_dir)
        X_tab_raw, y_raw, _ = loader.load_data()
        
        y = []
        for label in y_raw:
            if label == 0:
                y.append(self.class_map['Healthy'])
            elif label == 1:
                y.append(self.class_map['Warning']) # Tool Wear is a warning
            elif label == 2 or label == 3:
                y.append(self.class_map['Critical']) # Overstrain and Power Failure are critical
        
        y = np.array(y)
        
        X_vib = np.zeros((len(X_tab_raw), 2048, 1))
        X_curr = np.zeros((len(X_tab_raw), 2048, 3))
        
        y_rul = np.zeros(len(y))
        mask_rul = np.zeros(len(y))
        y_anomaly = (y != self.class_map['Healthy']).astype(int)
        
        return X_vib, X_curr, X_tab_raw, y, y_rul, mask_rul, y_anomaly

    def load_nasa(self):
        """Loads NASA data (Vibration + RUL)."""
        print("Loading NASA Dataset (2nd Test)...")
        test_dir = os.path.join(self.nasa_dir, '2nd_test', '2nd_test')
        if not os.path.exists(test_dir):
            print(f"NASA 2nd_test not found at {test_dir}")
            return np.array([]), np.array([]), np.array([]), np.array([]), np.array([]), np.array([]), np.array([])
            
        files = sorted(os.listdir(test_dir))
        num_files = len(files)
        
        X_vib = []
        y = []
        y_rul = []
        
        # Load a subset to save time/memory for this demo, or all if feasible.
        # 984 files * 20480 points is large. We'll take a snapshot from each file.
        # NASA files are 20480 points, 4 channels. We use Channel 0 (Bearing 1).
        
        for i, filename in enumerate(files):
            try:
                filepath = os.path.join(test_dir, filename)
                df = pd.read_csv(filepath, sep='\t', header=None)
                signal = df[0].values # Bearing 1
                
                # Take first 2048 points
                if len(signal) >= 2048:
                    X_vib.append(signal[:2048])
                    
                    # RUL: Linear degradation
                    rul = (num_files - i) / num_files # 1.0 -> 0.0
                    y_rul.append(rul)
                    
                    # SCIENTIFIC LABEL PROTOCOL (ISO 10816 / IEEE Failure Thresholds)
                    # We classify the life cycle into 'Healthy', 'Warning', and 'Critical'
                    if rul > 0.60:
                        y.append(self.class_map['Healthy'])
                    elif rul > 0.20:
                        y.append(self.class_map['Warning'])
                    else:
                        y.append(self.class_map['Critical'])
            except Exception as e:
                pass
                
        X_vib = np.array(X_vib).reshape(-1, 2048, 1)
        y = np.array(y)
        y_rul = np.array(y_rul)
        
        X_curr = np.zeros((len(X_vib), 2048, 3))
        X_tab = np.zeros((len(X_vib), 9))
        
        mask_rul = np.ones(len(y))
        y_anomaly = (y != self.class_map['Healthy']).astype(int)
        
        return X_vib, X_curr, X_tab, y, y_rul, mask_rul, y_anomaly

    def load_thermal(self):
        """Loads Thermal images from the test set."""
        print("Loading Thermal Dataset...")
        test_dir = os.path.join(self.thermal_dir, 'test')
        if not os.path.exists(test_dir):
            print(f"DEBUG: Thermal test dir not found at {test_dir}")
            return []
            
        images_base64 = []
        # We need a representative set. We'll grab up to 1000 images across classes.
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode('utf-8')
                            images_base64.append(encoded)
                    except:
                        pass
                if len(images_base64) >= 1000:
                    break
        print(f"Loaded {len(images_base64)} Thermal images.")
        return images_base64

    def prepare_data(self, split_ratio=(0.7, 0.15, 0.15)):
        """
        Loads, merges, and splits all datasets.

        DEPRECATED: Post-merge global shuffle breaks NASA temporal ordering and
        allows sliding-window leakage across train/test boundaries. Do not use
        this method for any reported publication metrics. See module docstring.
        """
        warnings.warn(
            "UniversalDataLoader.prepare_data() is deprecated and must NOT be used "
            "for publication metrics. It destroys NASA temporal ordering via global "
            "shuffle and does not enforce per-dataset train/test isolation. "
            "Use the official pipeline: build_latent_digital_twin.py -> "
            "generate_meta_features.py -> train_meta_fusion.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Load individual datasets
        X_vib_c, X_curr_c, X_tab_c, y_c, y_rul_c, mask_rul_c, y_anom_c = self.load_cwru()
        X_vib_cs, X_curr_cs, X_tab_cs, y_cs, y_rul_cs, mask_rul_cs, y_anom_cs = self.load_current_signature()
        X_vib_cia, X_curr_cia, X_tab_cia, y_cia, y_rul_cia, mask_rul_cia, y_anom_cia = self.load_cia1()
        X_vib_n, X_curr_n, X_tab_n, y_n, y_rul_n, mask_rul_n, y_anom_n = self.load_nasa()
        
        # Concatenate
        datasets = [
            (X_vib_c, X_curr_c, X_tab_c, y_c, y_rul_c, mask_rul_c, y_anom_c),
            (X_vib_cs, X_curr_cs, X_tab_cs, y_cs, y_rul_cs, mask_rul_cs, y_anom_cs),
            (X_vib_cia, X_curr_cia, X_tab_cia, y_cia, y_rul_cia, mask_rul_cia, y_anom_cia),
            (X_vib_n, X_curr_n, X_tab_n, y_n, y_rul_n, mask_rul_n, y_anom_n)
        ]
        
        # Filter out empty datasets
        datasets = [d for d in datasets if len(d[0]) > 0]
        
        X_vib = np.concatenate([d[0] for d in datasets], axis=0)
        X_curr = np.concatenate([d[1] for d in datasets], axis=0)
        X_tab = np.concatenate([d[2] for d in datasets], axis=0)
        y = np.concatenate([d[3] for d in datasets], axis=0)
        y_rul = np.concatenate([d[4] for d in datasets], axis=0)
        mask_rul = np.concatenate([d[5] for d in datasets], axis=0)
        y_anom = np.concatenate([d[6] for d in datasets], axis=0)
        
        # Load Thermal separately (as it is not aligned 1:1 with others)
        thermal_images = self.load_thermal()
        # Sparse Multimodal Fusion (Do not recycle images to prevent leakage)
        X_thermal = []
        if thermal_images:
            for i in range(len(y)):
                if i < len(thermal_images):
                    X_thermal.append(thermal_images[i])
                else:
                    X_thermal.append("") # Simulate sensor dropout / sparse data
        else:
            X_thermal = [""] * len(y)
        
        print(f"DEBUG: X_vib dtype: {X_vib.dtype}")
        print(f"DEBUG: X_curr dtype: {X_curr.dtype}")
        print(f"DEBUG: X_tab dtype: {X_tab.dtype}")
        print(f"DEBUG: y dtype: {y.dtype}")
        
        # Ensure float32
        X_vib = X_vib.astype(np.float32)
        X_curr = X_curr.astype(np.float32)
        X_tab = X_tab.astype(np.float32)
        y = y.astype(np.int32)
        y_rul = y_rul.astype(np.float32)
        mask_rul = mask_rul.astype(np.float32)
        y_anom = y_anom.astype(np.float32)
        
        # Create Masks
        mask_vib = (np.sum(np.abs(X_vib), axis=(1,2)) > 0).astype(int)
        mask_curr = (np.sum(np.abs(X_curr), axis=(1,2)) > 0).astype(int)
        mask_tab = (np.sum(np.abs(X_tab), axis=1) > 0).astype(int)
        
        masks = np.stack([mask_vib, mask_curr, mask_tab], axis=1)
        
        # GLOBAL SHUFFLE - Ensure test split contains a mix of all datasets and fault phases
        indices = np.arange(len(y))
        np.random.seed(42) # Reproducible for publication
        np.random.shuffle(indices)
        
        X_vib = X_vib[indices]
        X_curr = X_curr[indices]
        X_tab = X_tab[indices]
        y = y[indices]
        y_rul = y_rul[indices]
        mask_rul = mask_rul[indices]
        y_anom = y_anom[indices]
        masks = masks[indices]
        X_thermal = [X_thermal[i] for i in indices]
        
        # Split
        n_samples = len(y)
        train_end = int(n_samples * split_ratio[0])
        val_end = int(n_samples * (split_ratio[0] + split_ratio[1]))
        
        def get_split(arr):
            return arr[:train_end], arr[train_end:val_end], arr[val_end:]
            
        def get_split_list(lst):
            return lst[:train_end], lst[train_end:val_end], lst[val_end:]
            
        return {
            'train': {
                'vibration': get_split(X_vib)[0],
                'current': get_split(X_curr)[0],
                'tabular': get_split(X_tab)[0],
                'labels': to_categorical(get_split(y)[0], num_classes=self.num_classes),
                'rul': get_split(y_rul)[0],
                'anomaly': get_split(y_anom)[0],
                'masks': get_split(masks)[0],
                'mask_rul': get_split(mask_rul)[0]
            },
            'val': {
                'vibration': get_split(X_vib)[1],
                'current': get_split(X_curr)[1],
                'tabular': get_split(X_tab)[1],
                'labels': to_categorical(get_split(y)[1], num_classes=self.num_classes),
                'rul': get_split(y_rul)[1],
                'anomaly': get_split(y_anom)[1],
                'masks': get_split(masks)[1],
                'mask_rul': get_split(mask_rul)[1]
            },
            'test': {
                'vibration': get_split(X_vib)[2],
                'current': get_split(X_curr)[2],
                'tabular': get_split(X_tab)[2],
                'labels': to_categorical(get_split(y)[2], num_classes=self.num_classes),
                'rul': get_split(y_rul)[2],
                'anomaly': get_split(y_anom)[2],
                'masks': get_split(masks)[2],
                'mask_rul': get_split(mask_rul)[2],
                'thermal': get_split_list(X_thermal)[2]
            }
        }

if __name__ == "__main__":
    base_dir = r"d:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes"
    loader = UniversalDataLoader(base_dir)
    data = loader.prepare_data()
    
    print("\nUniversal Data Loaded and Split:")
    for split in ['train', 'val', 'test']:
        print(f"\n{split.upper()} Set:")
        print(f"  Vibration: {data[split]['vibration'].shape}")
        print(f"  Current:   {data[split]['current'].shape}")
        print(f"  Tabular:   {data[split]['tabular'].shape}")
        print(f"  Labels:    {data[split]['labels'].shape}")
        print(f"  RUL:       {data[split]['rul'].shape}")
        print(f"  Anomaly:   {data[split]['anomaly'].shape}")
        print(f"  Masks:     {data[split]['masks'].shape}")
