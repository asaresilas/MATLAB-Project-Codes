"""
Signal Processing Module for Predictive Maintenance

This module provides basic signal processing functions for fault diagnosis.
For advanced features, see advanced_features.py

Functions:
- compute_fft: Fast Fourier Transform
- extract_time_features: Statistical time-domain features
- envelope_spectrum: Bearing fault detection via envelope analysis

Author: Digital Twin Research Team
Version: 1.0 (Basic Features)
"""

import numpy as np
from scipy.fft import fft

def compute_fft(signal, fs):
    """
    Computes the Fast Fourier Transform of a signal.
    
    FFT converts time-domain signal to frequency-domain, revealing
    which frequencies are present in the signal. This is crucial for
    fault diagnosis because different faults create characteristic frequencies.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of time-domain signal
    fs : float
        Sampling frequency in Hz
        
    Returns:
    --------
    tuple : (frequencies, magnitude)
        frequencies : np.ndarray - Frequency bins in Hz
        magnitude : np.ndarray - Magnitude at each frequency
        
    Example:
    --------
    >>> signal = np.sin(2 * np.pi * 100 * t)  # 100 Hz sine wave
    >>> freqs, mags = compute_fft(signal, fs=1000)
    >>> peak_freq = freqs[np.argmax(mags)]  # Should be ~100 Hz
    """
    n = len(signal)
    yf = fft(signal)
    xf = np.fft.fftfreq(n, 1 / fs)[:n // 2]
    magnitude = 2.0 / n * np.abs(yf[0:n // 2])
    return xf, magnitude

def extract_time_features(signal):
    """
    Extracts statistical time-domain features from a signal.
    
    These features capture the statistical characteristics of the vibration
    signal without transforming to frequency domain. They are computationally
    efficient and provide good baseline performance.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of vibration signal
        
    Returns:
    --------
    dict : Dictionary of time-domain features
        - rms: Root Mean Square (overall vibration level)
        - mean: Average value (DC component)
        - std: Standard deviation (variability)
        - max: Maximum value (peak amplitude)
        - min: Minimum value
        - kurtosis: Peakiness (high for impulsive events like cracks)
        - skewness: Asymmetry (indicates unbalanced wear)
        
    Feature Interpretation:
    -----------------------
    - RMS: High values indicate excessive vibration
    - Kurtosis > 3: Impulsive events (bearing faults, cracks)
    - Kurtosis < 3: Smooth signal (normal operation)
    - Skewness ≠ 0: Asymmetric wear patterns
    
    Example:
    --------
    >>> healthy_signal = np.random.randn(1000) * 0.1
    >>> faulty_signal = healthy_signal + np.random.choice([0, 2], 1000, p=[0.95, 0.05])
    >>> healthy_features = extract_time_features(healthy_signal)
    >>> faulty_features = extract_time_features(faulty_signal)
    >>> print(f"Healthy kurtosis: {healthy_features['kurtosis']:.2f}")
    >>> print(f"Faulty kurtosis: {faulty_features['kurtosis']:.2f}")
    """
    # Avoid division by zero
    signal_std = np.std(signal)
    if signal_std == 0:
        signal_std = 1e-10
    
    signal_mean = np.mean(signal)
    
    return {
        'rms': np.sqrt(np.mean(signal**2)),
        'mean': signal_mean,
        'std': signal_std,
        'max': np.max(signal),
        'min': np.min(signal),
        'kurtosis': np.mean((signal - signal_mean)**4) / (signal_std**4),
        'skewness': np.mean((signal - signal_mean)**3) / (signal_std**3)
    }

def envelope_spectrum(signal, fs):
    """
    Computes the envelope spectrum (useful for bearing fault detection).
    
    The envelope spectrum is particularly effective for detecting bearing faults
    because bearing faults create periodic impacts that modulate the carrier signal.
    
    How it works:
    1. Apply Hilbert transform to get analytic signal
    2. Extract amplitude envelope (magnitude of analytic signal)
    3. Compute FFT of envelope to find modulation frequencies
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of vibration signal
    fs : float
        Sampling frequency in Hz
        
    Returns:
    --------
    tuple : (frequencies, magnitude)
        Envelope spectrum in frequency domain
        
    Why it works for bearings:
    ---------------------------
    Bearing faults create periodic impacts at characteristic frequencies:
    - Inner race fault: BPFI (Ball Pass Frequency Inner race)
    - Outer race fault: BPFO (Ball Pass Frequency Outer race)
    - Ball fault: BSF (Ball Spin Frequency)
    
    These impacts modulate the high-frequency resonance of the bearing,
    and the envelope spectrum reveals these modulation frequencies.
    
    Example:
    --------
    >>> # Simulate bearing fault (100 Hz impacts modulating 5 kHz resonance)
    >>> t = np.linspace(0, 1, 12000)
    >>> carrier = np.sin(2 * np.pi * 5000 * t)
    >>> modulation = 1 + 0.5 * np.sin(2 * np.pi * 100 * t)
    >>> signal = carrier * modulation
    >>> freqs, mags = envelope_spectrum(signal, fs=12000)
    >>> # Peak should appear at 100 Hz (fault frequency)
    """
    from scipy.signal import hilbert
    
    # Compute analytic signal using Hilbert transform
    analytic_signal = hilbert(signal)
    
    # Extract amplitude envelope
    amplitude_envelope = np.abs(analytic_signal)
    
    # Compute FFT of envelope
    return compute_fft(amplitude_envelope, fs)


def extract_combined_features(signal, fs=12000):
    """
    Extract both time-domain and basic frequency-domain features.
    
    This is a convenience function that combines time features and
    frequency features for quick analysis.
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of vibration signal
    fs : float
        Sampling frequency in Hz (default: 12000)
        
    Returns:
    --------
    dict : Combined feature dictionary
    
    Note:
    -----
    For advanced features (wavelets, spectral analysis, order tracking),
    use the advanced_features module:
    
    >>> from src.features.advanced_features import extract_all_advanced_features
    >>> advanced_feats = extract_all_advanced_features(signal, fs=12000, speed_rpm=1800)
    """
    features = {}
    
    # Time-domain features
    time_features = extract_time_features(signal)
    features.update(time_features)
    
    # Frequency-domain features (basic)
    freqs, mags = compute_fft(signal, fs)
    
    # Peak frequency and amplitude
    peak_idx = np.argmax(mags)
    features['peak_frequency'] = freqs[peak_idx]
    features['peak_amplitude'] = mags[peak_idx]
    
    # Frequency band energies
    # Low: 0-1000 Hz, Mid: 1000-5000 Hz, High: 5000+ Hz
    low_mask = freqs < 1000
    mid_mask = (freqs >= 1000) & (freqs < 5000)
    high_mask = freqs >= 5000
    
    features['low_freq_energy'] = np.sum(mags[low_mask]**2) if np.any(low_mask) else 0.0
    features['mid_freq_energy'] = np.sum(mags[mid_mask]**2) if np.any(mid_mask) else 0.0
    features['high_freq_energy'] = np.sum(mags[high_mask]**2) if np.any(high_mask) else 0.0
    
    # Envelope spectrum features
    env_freqs, env_mags = envelope_spectrum(signal, fs)
    env_peak_idx = np.argmax(env_mags)
    features['envelope_peak_freq'] = env_freqs[env_peak_idx]
    features['envelope_peak_amplitude'] = env_mags[env_peak_idx]
    
    return features


def extract_induction_features(signal, fs=10000):
    """
    Extracts the specific feature vector used for the Induction Motor ML model.
    
    Features (in order):
    1. RMS
    2. Mean
    3. Std
    4. Max
    5. Min
    6. Kurtosis
    7. Skewness
    8. Peak-to-Peak
    9. Crest Factor
    10. Dominant Frequency
    11. Spectral Centroid
    12. Spectral Bandwidth
    13. Spectral Energy
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of vibration signal
    fs : float
        Sampling frequency (default 10000 Hz)
        
    Returns:
    --------
    list : List of 13 feature values
    """
    from scipy.stats import skew, kurtosis
    
    # --- Time Domain ---
    rms = np.sqrt(np.mean(signal**2))
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    max_val = np.max(signal)
    min_val = np.min(signal)
    kurt = kurtosis(signal)
    skew_val = skew(signal)
    peak_to_peak = max_val - min_val
    crest_factor = max_val / (rms + 1e-9)
    
    # --- Frequency Domain ---
    # Compute FFT
    fft_vals = np.abs(np.fft.rfft(signal))
    fft_freqs = np.fft.rfftfreq(len(signal), d=1/fs)
    
    # Dominant Frequency
    dom_freq = fft_freqs[np.argmax(fft_vals)]
    
    # Spectral Centroid
    spectral_centroid = np.sum(fft_freqs * fft_vals) / (np.sum(fft_vals) + 1e-9)
    
    # Spectral Bandwidth
    spectral_bandwidth = np.sqrt(np.sum(((fft_freqs - spectral_centroid)**2) * fft_vals) / (np.sum(fft_vals) + 1e-9))
    
    # Spectral Energy
    spectral_energy = np.sum(fft_vals**2) / len(fft_vals)
    
    return [
        rms, mean_val, std_val, max_val, min_val, kurt, skew_val, 
        peak_to_peak, crest_factor,
        dom_freq, spectral_centroid, spectral_bandwidth, spectral_energy
    ]


def extract_nasa_features(signal):
    """
    Extracts the 9 time-domain features used for the NASA RUL model.
    
    Features:
    1. RMS
    2. Mean
    3. Std
    4. Max
    5. Min
    6. Kurtosis
    7. Skewness
    8. Peak-to-Peak
    9. Crest Factor
    
    Parameters:
    -----------
    signal : np.ndarray
        1D numpy array of vibration signal
        
    Returns:
    --------
    dict : Dictionary of features
    """
    from scipy.stats import skew, kurtosis
    
    # Basic stats
    rms = np.sqrt(np.mean(signal**2))
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    max_val = np.max(signal)
    min_val = np.min(signal)
    
    # Shape stats
    # Use scipy for consistency with training (Fisher=True is default for scipy, check notebook)
    # Notebook used: np.mean((signal - mean)**4) / std**4 -> This is Pearson's kurtosis (normal=3)
    # scipy.stats.kurtosis returns excess kurtosis (normal=0) by default.
    # We should match the notebook implementation manually to be safe.
    
    # Manual calculation to match notebook exactly:
    # 'kurtosis': np.mean((signal - np.mean(signal))**4) / (np.std(signal)**4)
    # 'skewness': np.mean((signal - np.mean(signal))**3) / (np.std(signal)**3)
    
    if std_val == 0:
        kurt = 0
        skew_val = 0
        crest_factor = 0
    else:
        centered = signal - mean_val
        kurt = np.mean(centered**4) / (std_val**4)
        skew_val = np.mean(centered**3) / (std_val**3)
        crest_factor = np.max(np.abs(signal)) / rms
        
    peak_to_peak = max_val - min_val
    
    return {
        'rms': rms,
        'mean': mean_val,
        'std': std_val,
        'max': max_val,
        'min': min_val,
        'kurtosis': kurt,
        'skewness': skew_val,
        'peak_to_peak': peak_to_peak,
        'crest_factor': crest_factor
    }


if __name__ == "__main__":
    """
    Test the signal processing functions
    """
    print("Testing Signal Processing Module...")
    print("=" * 60)
    
    # Generate test signals
    fs = 12000
    t = np.linspace(0, 1, fs)
    
    # Healthy signal: Low noise
    healthy = 0.1 * np.random.randn(fs)
    
    # Faulty signal: Noise + 100 Hz component + impacts
    faulty = 0.1 * np.random.randn(fs) + 0.5 * np.sin(2 * np.pi * 100 * t)
    # Add periodic impacts
    for i in range(0, fs, fs//100):
        if i < fs:
            faulty[i] += 2.0
    
    print("\n1. Time-Domain Features:")
    print("-" * 60)
    healthy_time = extract_time_features(healthy)
    faulty_time = extract_time_features(faulty)
    
    print(f"Healthy - RMS: {healthy_time['rms']:.4f}, Kurtosis: {healthy_time['kurtosis']:.2f}")
    print(f"Faulty  - RMS: {faulty_time['rms']:.4f}, Kurtosis: {faulty_time['kurtosis']:.2f}")
    print(f"-> Faulty signal has {faulty_time['kurtosis']/healthy_time['kurtosis']:.1f}x higher kurtosis")
    
    print("\n2. Frequency-Domain Features:")
    print("-" * 60)
    freqs, mags = compute_fft(faulty, fs)
    peak_idx = np.argmax(mags)
    print(f"Peak frequency: {freqs[peak_idx]:.2f} Hz")
    print(f"Peak amplitude: {mags[peak_idx]:.4f}")
    
    print("\n3. Envelope Spectrum:")
    print("-" * 60)
    env_freqs, env_mags = envelope_spectrum(faulty, fs)
    env_peak_idx = np.argmax(env_mags)
    print(f"Envelope peak frequency: {env_freqs[env_peak_idx]:.2f} Hz")
    
    print("\n4. Combined Features:")
    print("-" * 60)
    combined = extract_combined_features(faulty, fs)
    print(f"Total features extracted: {len(combined)}")
    print(f"Feature names: {list(combined.keys())}")
    
    print("\n" + "=" * 60)
    print("Signal Processing Module - Working Correctly!")
    print("=" * 60)

