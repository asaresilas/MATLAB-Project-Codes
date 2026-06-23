import os
import glob
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

class CurrentSignatureLoader:
    def __init__(self, data_dir):
        """
        Loader for the Mendeley 'Current Signature Dataset'.
        
        Args:
            data_dir (str): Path to the root directory containing the fault folders.
                            e.g., '.../Current Signature Dataset of Three-Phase Induction Motor...'
        """
        self.data_dir = data_dir
        self.classes = [
            'healthy', 
            'bearing_fault', 
            'broken_rotor_bar'
        ]

    def _extract_features(self, signal):
        """
        Extracts statistical time-domain features from a 1D signal.
        """
        # Replace NaNs in signal with 0 to prevent propagation
        signal = np.nan_to_num(signal)
        
        features = {}
        features['mean'] = np.mean(signal)
        features['std'] = np.std(signal)
        features['rms'] = np.sqrt(np.mean(signal**2))
        features['max'] = np.max(signal)
        features['min'] = np.min(signal)
        
        # Handle constant signal (std=0) which causes NaN in kurtosis/skew
        if features['std'] == 0:
            features['kurtosis'] = 0.0
            features['skewness'] = 0.0
        else:
            features['kurtosis'] = kurtosis(signal)
            features['skewness'] = skew(signal)
            
        features['peak_to_peak'] = features['max'] - features['min']
        # Crest Factor: Peak / RMS
        features['crest_factor'] = features['max'] / (features['rms'] + 1e-9)
        
        # Final safety check for any remaining NaNs or Infs
        for k, v in features.items():
            if np.isnan(v) or np.isinf(v):
                features[k] = 0.0
                
        return features

    def load_data(self):
        """
        Loads data from all subdirectories, extracts features, and returns X, y.
        
        Returns:
            X (pd.DataFrame): Feature matrix.
            y (np.array): Labels.
        """
        all_features = []
        labels = []
        
        # Get all subdirectories
        subdirs = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))]
        
        print(f"Found {len(subdirs)} folders in {self.data_dir}")
        
        for folder in subdirs:
            folder_path = os.path.join(self.data_dir, folder)
            
            # Determine label from folder name
            label = 'unknown'
            if 'healthy' in folder.lower():
                label = 'healthy'
            elif 'bearing-fault' in folder.lower():
                label = 'bearing_fault' # We can be more specific later (e.g., 0.7mm)
            elif 'broken-rotor-bar' in folder.lower():
                label = 'broken_rotor_bar'
            
            print(f"Processing folder: {folder} -> Label: {label}")
            
            # Find CSV files
            csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
            
            for file_path in csv_files:
                try:
                    # Load CSV (Skip bad lines if any)
                    df = pd.read_csv(file_path)
                    
                    # Columns: Time Stamp, Current-A, Current-B, Current-C
                    # We will extract features for each Phase (A, B, C)
                    
                    # Clean column names (strip spaces)
                    df.columns = [c.strip() for c in df.columns]
                    
                    phases = ['Current-A', 'Current-B', 'Current-C']
                    
                    # Check if columns exist
                    if not all(col in df.columns for col in phases):
                        print(f"  WARNING: Missing columns in {os.path.basename(file_path)}. Skipping.")
                        continue
                        
                    # Extract features for this file (treating the whole file as one sample for now? 
                    # Or should we window it? The file is 3.5MB, likely long. 
                    # For ML, we usually split into windows. Let's window it.)
                    
                    # Windowing parameters
                    window_size = 1000 # Approx 1 second if 1kHz? (Timestamp suggests >1kHz actually)
                    stride = 1000 # Non-overlapping for now
                    
                    num_samples = len(df)
                    for start in range(0, num_samples - window_size, stride):
                        window = df.iloc[start:start+window_size]
                        
                        sample_features = {}
                        
                        for phase in phases:
                            signal = window[phase].values
                            feats = self._extract_features(signal)
                            # Prefix with phase name
                            for k, v in feats.items():
                                sample_features[f"{phase}_{k}"] = v
                        
                        all_features.append(sample_features)
                        labels.append(label)
                        
                except Exception as e:
                    print(f"  ERROR reading {file_path}: {e}")
        
        print(f"\nTotal CSV files processed: {len(all_features) // (len(all_features)//len(csv_files) if len(csv_files)>0 and len(all_features)>0 else 1)} (Estimate based on windows)") 
        # Actually, let's just count files properly
        total_files = sum([len(glob.glob(os.path.join(self.data_dir, d, "*.csv"))) for d in subdirs])
        print(f"Total CSV files found in directories: {total_files}")
        
        
        X = pd.DataFrame(all_features)
        y = np.array(labels)
        
        return X, y

    def load_raw_data(self, window_size=1000, stride=1000):
        """
        Loads raw time-series data for Deep Learning.
        
        Args:
            window_size (int): Number of time steps per window.
            stride (int): Stride for windowing.
            
        Returns:
            X (np.array): 3D array of shape (num_samples, window_size, 3).
                          Channels: [Current-A, Current-B, Current-C]
            y (np.array): Labels.
        """
        all_windows = []
        labels = []
        
        subdirs = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))]
        
        print(f"Found {len(subdirs)} folders for Raw Data Loading...")
        
        for folder in subdirs:
            folder_path = os.path.join(self.data_dir, folder)
            
            # Determine label
            label = 'unknown'
            if 'healthy' in folder.lower():
                label = 'healthy'
            elif 'bearing-fault' in folder.lower():
                label = 'bearing_fault'
            elif 'broken-rotor-bar' in folder.lower():
                label = 'broken_rotor_bar'
            
            print(f"Processing folder: {folder} -> Label: {label}")
            
            csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
            
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path)
                    df.columns = [c.strip() for c in df.columns]
                    
                    phases = ['Current-A', 'Current-B', 'Current-C']
                    
                    if not all(col in df.columns for col in phases):
                        continue
                        
                    # Extract raw signals
                    signals = df[phases].values # Shape: (Total_Time, 3)
                    
                    # Windowing
                    num_samples = len(signals)
                    for start in range(0, num_samples - window_size, stride):
                        window = signals[start:start+window_size]
                        
                        # Ensure window is full size
                        if len(window) == window_size:
                            all_windows.append(window)
                            labels.append(label)
                            
                except Exception as e:
                    print(f"  ERROR reading {file_path}: {e}")
        
        X = np.array(all_windows)
        y = np.array(labels)
        
        print(f"Raw Data Loaded: X shape={X.shape}, y shape={y.shape}")
        return X, y

if __name__ == "__main__":
    # Test the loader
    base_dir = r"d:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Current Signature Data/Current Signature Dataset of Three-Phase Induction Motor under Varying Load Conditions"
    loader = CurrentSignatureLoader(base_dir)
    X, y = loader.load_data()
    print(f"Loaded Data: X shape={X.shape}, y shape={y.shape}")
    print("Class counts:", np.unique(y, return_counts=True))
