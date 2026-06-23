import os
import pandas as pd
import scipy.io
import numpy as np

class CWRULoader:
    """
    Loader for Case Western Reserve University (CWRU) Bearing Data.
    Expected format: .mat files containing vibration time-series.
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def load_file(self, filename):
        """Loads a single .mat file and returns the vibration signal."""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        mat_data = scipy.io.loadmat(filepath)
        # Logic to find the vibration data key (usually ends with DE_time or FE_time)
        for key in mat_data.keys():
            if 'DE_time' in key: # Drive End
                return mat_data[key].flatten()
            elif 'FE_time' in key: # Fan End
                return mat_data[key].flatten()
        
        raise ValueError(f"No vibration data found in {filename}")

class NASALoader:
    """
    Loader for NASA IMS Bearing Dataset.
    Expected format: Directory of files where each file is a snapshot of vibration data.
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def load_snapshot(self, filename):
        """Loads a single snapshot file (tab-separated)."""
        filepath = os.path.join(self.data_dir, filename)
        # NASA data is typically 4 columns: Bearing 1, 2, 3, 4
        df = pd.read_csv(filepath, sep='\t', header=None)
        return df.values

class TabularLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def load_file(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        # Assuming CSV for now based on typical Zenodo datasets, but can adapt
        if filename.endswith('.mat'):
             mat_data = scipy.io.loadmat(filepath)
             # Placeholder key, needs actual inspection
             return mat_data['current'].flatten() 
        else:
            return pd.read_csv(filepath).values

class InductionMotorLoader:
    """
    Loader for the IEEE Induction Motor Dataset (Treml et al.).
    Format: Large .mat files (v7.3 / HDF5) containing high-res signals.
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.class_map = {
            'struct_rs_R1': 0,   # Healthy
            'struct_r1b_R1': 1,  # Warning
            'struct_r2b_R1': 2,  # Critical
            'struct_r3b_R1': 2,
            'struct_r4b_R1': 2
        }

    def load_all_data(self, samples_per_class=1000, window_size=2048):
        """
        Extracts windows from the high-res .mat signals.
        """
        import h5py
        X = []
        y = []
        
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.mat'): continue
            
            struct_name = filename.split('.')[0]
            if struct_name not in self.class_map: continue
            
            label = self.class_map[struct_name]
            filepath = os.path.join(self.data_dir, filename)
            
            print(f"Processing {filename} (Label {label})...")
            try:
                with h5py.File(filepath, 'r') as f:
                    # In Treml's dataset, current is often in 'ia' or similar field
                    # We look for a 1D or 2D array that matches expected length
                    # Defaulting to first available large dataset if unknown
                    ds_name = list(f.keys())[0] if struct_name not in f else struct_name
                    raw_data = f[ds_name][:]
                    
                    # Handle transposed HDF5 data if necessary
                    if raw_data.shape[0] < raw_data.shape[1]:
                        raw_data = raw_data.T
                        
                    # Extract windows
                    total_len = len(raw_data)
                    for _ in range(samples_per_class):
                        start = np.random.randint(0, total_len - window_size)
                        X.append(raw_data[start:start+window_size, 0]) # Channel 0
                        y.append(label)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                            
        return np.array(X), np.array(y)

    def load_fft_features(self, normalized=True):
        """
        Loads pre-computed FFT features from the 'freq' directory.
        Args:
            normalized (bool): If True, load *_fft_norm.csv, else *_fft.csv
        Returns:
            X: Numpy array of features
            y: Numpy array of labels
        """
        # Assume freq dir is parallel to raw dir (data_dir)
        # data_dir = .../processed_data/raw
        # freq_dir = .../processed_data/freq
        freq_dir = os.path.abspath(os.path.join(self.data_dir, '..', 'freq'))
        
        if not os.path.exists(freq_dir):
            print(f"Warning: Frequency directory not found at {freq_dir}")
            return None, None
            
        suffix = '_fft_norm.csv' if normalized else '_fft.csv'
        
        X_all = []
        y_all = []
        
        # Map class names to filenames and labels
        # Note: The order here must match the order of raw files if we want to combine them directly.
        # Raw files are sorted alphabetically: damaged_1, damaged_2, damaged_ring, healthy
        
        class_files = {
            'damaged_1': f'signals_damaged_1{suffix}',
            'damaged_2': f'signals_damaged_2{suffix}',
            'damaged_ring': f'signals_damaged_ring{suffix}',
            'healthy': f'signals_healthy{suffix}'
        }
        
        # Iterate in a specific order to match labels
        for class_name, filename in class_files.items():
            filepath = os.path.join(freq_dir, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath)
                    # df shape is (N_samples, N_features)
                    features = df.values
                    label = self.classes[class_name]
                    
                    X_all.append(features)
                    y_all.extend([label] * len(features))
                    
                    print(f"Loaded {class_name} FFT features: {features.shape}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"Warning: File {filename} not found.")
                
        if X_all:
            return np.vstack(X_all), np.array(y_all)
        else:
            return np.array([]), np.array([])

    def load_raw_data_for_cnn(self, window_size=2048, stride=100):
        """
        Loads raw data and segments it for 1D CNN input.
        Returns:
            X: (Samples, Window_Size, 1)
            y: (Samples,)
        """
        X_raw, y_raw = self.load_all_data()
        
        X_windows = []
        y_windows = []
        
        for signal, label in zip(X_raw, y_raw):
            # Simple sliding window
            if len(signal) >= window_size:
                num_windows = (len(signal) - window_size) // stride + 1
                for i in range(num_windows):
                    start = i * stride
                    end = start + window_size
                    window = signal[start:end]
                    X_windows.append(window)
                    y_windows.append(label)
        
        X = np.array(X_windows)
        y = np.array(y_windows)
        
        # Reshape for CNN: (Samples, TimeSteps, Channels)
        if X.ndim == 2:
            X = X.reshape(X.shape[0], X.shape[1], 1)
            
        return X, y

    def load_fft_data_for_mlp(self):
        """
        Loads FFT features for MLP input.
        Returns:
            X: (Samples, Features)
            y: (Samples,)
        """
        # Reuse existing method, just ensure it's clean
        return self.load_fft_features(normalized=True)

class CIA1Loader:
    """
    Loader for CIA-1 Dataset (Predictive Maintenance).
    Format: CSV file with sensor readings and failure type labels.
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.csv_file = os.path.join(data_dir, 'CIA-1 Dataset - Dataset (1).csv')
        
        # Failure type mapping
        self.failure_types = {
            'No Failure': 0,
            'Tool Wear Failure': 1,
            'Overstrain Failure': 2,
            'Power Failure': 3
        }
        
    def load_data(self, return_raw=False):
        """
        Loads the CIA-1 dataset.
        
        Args:
            return_raw: If True, returns the raw DataFrame without preprocessing
            
        Returns:
            X: Feature array (n_samples, n_features)
            y: Label array (n_samples,)
            feature_names: List of feature names
        """
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        df = pd.read_csv(self.csv_file)
        
        if return_raw:
            return df
        
        # Drop ID columns
        df = df.drop(['UDI', 'Product ID'], axis=1)
        
        # Encode categorical 'Type' feature (L/M/H)
        type_dummies = pd.get_dummies(df['Type'], prefix='Type')
        df = pd.concat([df.drop('Type', axis=1), type_dummies], axis=1)
        
        # Extract labels
        y = df['Failure Type'].map(self.failure_types).values
        
        # Drop target column
        X = df.drop('Failure Type', axis=1).values
        feature_names = df.drop('Failure Type', axis=1).columns.tolist()
        
        print(f"Loaded CIA-1 Dataset: {X.shape[0]} samples, {X.shape[1]} features")
        print(f"Class distribution: {pd.Series(y).value_counts().sort_index().to_dict()}")
        
        return X, y, feature_names
    
    def get_class_names(self):
        """Returns the list of class names in order."""
        return ['No Failure', 'Tool Wear Failure', 'Overstrain Failure', 'Power Failure']

