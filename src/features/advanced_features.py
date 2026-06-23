"""
Advanced Feature Extraction Module for Predictive Maintenance

This module implements advanced signal processing techniques for fault diagnosis:
- Wavelet Transform Features: Multi-scale time-frequency analysis
- Spectral Features: Frequency domain characteristics
- Envelope Spectrum: Bearing fault detection
- Order Tracking: Speed-normalized analysis

Author: Digital Twin Research Team
Date: 2025-11-21
"""

import numpy as np
import pywt
from scipy import signal
from scipy.stats import entropy
from scipy.signal import hilbert, welch
from typing import Dict, Tuple, Optional


class WaveletFeatureExtractor:
    """
    Wavelet Transform Feature Extraction
    
    Wavelets are superior to FFT for non-stationary signals because they provide
    both time and frequency localization. This is crucial for detecting transient
    faults that occur at specific times.
    
    Parameters:
    -----------
    wavelet : str
        Wavelet type (default: 'db4' - Daubechies 4)
        Other options: 'db8', 'sym5', 'coif3'
    level : int
        Decomposition level (default: 5)
        Higher levels capture lower frequencies
    """
    
    def __init__(self, wavelet: str = 'db4', level: int = 5):
        self.wavelet = wavelet
        self.level = level
    
    def extract_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """
        Extract wavelet-based features from signal
        
        Parameters:
        -----------
        signal_data : np.ndarray
            Input vibration signal
            
        Returns:
        --------
        dict : Dictionary of wavelet features
        
        Features Explained:
        - Energy at each level: Indicates fault severity at different frequency bands
        - Entropy at each level: Measures randomness/disorder at each scale
        - Energy ratio: Relative energy distribution across scales
        """
        features = {}
        
        # Perform wavelet decomposition
        # Returns: [cA_n, cD_n, cD_n-1, ..., cD_1]
        # cA_n: Approximation coefficients (low frequency)
        # cD_i: Detail coefficients (high frequency)
        coeffs = pywt.wavedec(signal_data, self.wavelet, level=self.level)
        
        # Calculate energy at each level
        # Energy = sum of squared coefficients
        # High energy at a level indicates strong signal content at that frequency band
        for i, coeff in enumerate(coeffs):
            level_name = f'level_{i}' if i > 0 else 'approximation'
            
            # Energy
            features[f'wavelet_energy_{level_name}'] = np.sum(coeff**2)
            
            # Entropy (measure of randomness)
            # Low entropy: Tonal/periodic (specific fault frequencies)
            # High entropy: Random/noisy (general degradation)
            coeff_abs = np.abs(coeff)
            if np.sum(coeff_abs) > 0:
                coeff_normalized = coeff_abs / np.sum(coeff_abs)
                features[f'wavelet_entropy_{level_name}'] = entropy(coeff_normalized)
            else:
                features[f'wavelet_entropy_{level_name}'] = 0.0
            
            # Statistical features of coefficients
            features[f'wavelet_mean_{level_name}'] = np.mean(np.abs(coeff))
            features[f'wavelet_std_{level_name}'] = np.std(coeff)
            features[f'wavelet_max_{level_name}'] = np.max(np.abs(coeff))
        
        # Total energy
        total_energy = sum([features[k] for k in features.keys() if 'energy' in k])
        
        # Energy ratios (relative energy at each level)
        # Helps identify which frequency bands are dominant
        for i in range(len(coeffs)):
            level_name = f'level_{i}' if i > 0 else 'approximation'
            energy_key = f'wavelet_energy_{level_name}'
            if total_energy > 0:
                features[f'wavelet_energy_ratio_{level_name}'] = features[energy_key] / total_energy
            else:
                features[f'wavelet_energy_ratio_{level_name}'] = 0.0
        
        return features


class SpectralFeatureExtractor:
    """
    Spectral (Frequency Domain) Feature Extraction
    
    Analyzes the frequency content of signals to identify fault signatures.
    Different faults create characteristic frequency patterns.
    
    Parameters:
    -----------
    fs : float
        Sampling frequency in Hz
    nperseg : int
        Length of each segment for Welch's method (default: 1024)
    """
    
    def __init__(self, fs: float = 12000, nperseg: int = 1024):
        self.fs = fs
        self.nperseg = nperseg
    
    def extract_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """
        Extract spectral features from signal
        
        Parameters:
        -----------
        signal_data : np.ndarray
            Input vibration signal
            
        Returns:
        --------
        dict : Dictionary of spectral features
        """
        features = {}
        
        # Compute Power Spectral Density using Welch's method
        # Welch's method: Averages multiple FFTs to reduce noise
        freqs, psd = welch(signal_data, self.fs, nperseg=self.nperseg)
        
        # Normalize PSD for probability-like interpretation
        psd_normalized = psd / np.sum(psd)
        
        # 1. Spectral Centroid (Center of mass of spectrum)
        # Interpretation: "Average" frequency
        # High value: High-frequency content (severe/high-speed faults)
        # Low value: Low-frequency content (slow degradation)
        features['spectral_centroid'] = np.sum(freqs * psd_normalized)
        
        # 2. Spectral Spread (Standard deviation of spectrum)
        # Interpretation: How spread out the frequencies are
        # High value: Broadband noise (multiple faults, general wear)
        # Low value: Narrow-band (specific fault frequencies)
        mean_freq = features['spectral_centroid']
        features['spectral_spread'] = np.sqrt(
            np.sum(((freqs - mean_freq)**2) * psd_normalized)
        )
        
        # 3. Spectral Entropy
        # Interpretation: Randomness of frequency distribution
        # Low value: Tonal/harmonic (specific fault frequencies)
        # High value: White noise (random degradation)
        features['spectral_entropy'] = entropy(psd_normalized)
        
        # 4. Spectral Flatness (Wiener entropy)
        # Ratio of geometric mean to arithmetic mean
        # Near 0: Tonal signal
        # Near 1: White noise
        geometric_mean = np.exp(np.mean(np.log(psd + 1e-10)))
        arithmetic_mean = np.mean(psd)
        features['spectral_flatness'] = geometric_mean / (arithmetic_mean + 1e-10)
        
        # 5. Peak Frequency
        # The dominant frequency in the signal
        peak_idx = np.argmax(psd)
        features['peak_frequency'] = freqs[peak_idx]
        features['peak_amplitude'] = psd[peak_idx]
        
        # 6. Frequency Band Powers
        # Different faults appear in different frequency ranges
        # Low: 0-1000 Hz (slow mechanical issues)
        # Mid: 1000-5000 Hz (bearing faults)
        # High: 5000+ Hz (high-speed impacts, severe faults)
        low_freq_mask = freqs < 1000
        mid_freq_mask = (freqs >= 1000) & (freqs < 5000)
        high_freq_mask = freqs >= 5000
        
        features['low_freq_power'] = np.sum(psd[low_freq_mask])
        features['mid_freq_power'] = np.sum(psd[mid_freq_mask])
        features['high_freq_power'] = np.sum(psd[high_freq_mask])
        
        # Power ratios
        total_power = np.sum(psd)
        if total_power > 0:
            features['low_freq_ratio'] = features['low_freq_power'] / total_power
            features['mid_freq_ratio'] = features['mid_freq_power'] / total_power
            features['high_freq_ratio'] = features['high_freq_power'] / total_power
        else:
            features['low_freq_ratio'] = 0.0
            features['mid_freq_ratio'] = 0.0
            features['high_freq_ratio'] = 0.0
        
        # 7. Spectral Kurtosis (measure of impulsiveness in frequency domain)
        features['spectral_kurtosis'] = np.mean((psd - np.mean(psd))**4) / (np.std(psd)**4 + 1e-10)
        
        # 8. Spectral Skewness (asymmetry of spectrum)
        features['spectral_skewness'] = np.mean((psd - np.mean(psd))**3) / (np.std(psd)**3 + 1e-10)
        
        return features


class EnvelopeSpectrumExtractor:
    """
    Envelope Spectrum Analysis for Bearing Fault Detection
    
    The envelope spectrum is particularly effective for bearing fault detection
    because bearing faults create periodic impacts that modulate the signal.
    
    How it works:
    1. Bandpass filter to isolate bearing fault frequencies
    2. Hilbert transform to get amplitude envelope
    3. FFT of envelope to find modulation frequencies
    
    Parameters:
    -----------
    fs : float
        Sampling frequency in Hz
    filter_band : tuple
        Bandpass filter range (low, high) in Hz
        Default: (1000, 5000) - typical bearing fault range
    """
    
    def __init__(self, fs: float = 12000, filter_band: Tuple[float, float] = (1000, 5000)):
        self.fs = fs
        self.filter_band = filter_band
    
    def extract_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """
        Extract envelope spectrum features
        
        Parameters:
        -----------
        signal_data : np.ndarray
            Input vibration signal
            
        Returns:
        --------
        dict : Dictionary of envelope features
        """
        features = {}
        
        # 1. Bandpass filter
        # Isolate frequency range where bearing faults appear
        nyquist = self.fs / 2
        low = self.filter_band[0] / nyquist
        high = self.filter_band[1] / nyquist
        
        # Design Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band')
        filtered_signal = signal.filtfilt(b, a, signal_data)
        
        # 2. Hilbert Transform
        # Get analytic signal (complex signal with amplitude and phase)
        analytic_signal = hilbert(filtered_signal)
        
        # 3. Amplitude Envelope
        # The magnitude of the analytic signal
        amplitude_envelope = np.abs(analytic_signal)
        
        # 4. Envelope Spectrum (FFT of envelope)
        envelope_fft = np.fft.fft(amplitude_envelope)
        envelope_freqs = np.fft.fftfreq(len(amplitude_envelope), 1/self.fs)
        
        # Take positive frequencies only
        positive_freq_idx = envelope_freqs > 0
        envelope_freqs = envelope_freqs[positive_freq_idx]
        envelope_magnitude = np.abs(envelope_fft[positive_freq_idx])
        
        # 5. Extract features from envelope spectrum
        
        # Peak in envelope spectrum (characteristic fault frequency)
        peak_idx = np.argmax(envelope_magnitude)
        features['envelope_peak_freq'] = envelope_freqs[peak_idx]
        features['envelope_peak_amplitude'] = envelope_magnitude[peak_idx]
        
        # Energy in envelope
        features['envelope_energy'] = np.sum(amplitude_envelope**2)
        
        # Statistical features of envelope
        features['envelope_mean'] = np.mean(amplitude_envelope)
        features['envelope_std'] = np.std(amplitude_envelope)
        features['envelope_max'] = np.max(amplitude_envelope)
        features['envelope_rms'] = np.sqrt(np.mean(amplitude_envelope**2))
        
        # Envelope kurtosis (impulsiveness)
        # High kurtosis indicates periodic impacts (bearing faults)
        features['envelope_kurtosis'] = np.mean((amplitude_envelope - np.mean(amplitude_envelope))**4) / (np.std(amplitude_envelope)**4 + 1e-10)
        
        # Crest factor of envelope
        # Ratio of peak to RMS
        # High crest factor indicates impulsive events
        features['envelope_crest_factor'] = features['envelope_max'] / (features['envelope_rms'] + 1e-10)
        
        return features


class OrderTrackingExtractor:
    """
    Order Tracking for Variable Speed Analysis
    
    Problem: Motor speed varies → fault frequencies vary
    Solution: Analyze in "orders" (multiples of shaft speed) instead of Hz
    
    Example:
    - Shaft speed: 1800 RPM = 30 Hz
    - Inner race fault: 5.2× shaft speed = 156 Hz
    - If speed changes to 1500 RPM (25 Hz) → fault at 130 Hz
    - Order analysis: Always 5.2× order (speed-independent)
    
    Parameters:
    -----------
    bearing_geometry : dict
        Bearing geometry parameters for calculating fault orders
        Keys: 'ball_diameter', 'pitch_diameter', 'num_balls', 'contact_angle'
    """
    
    def __init__(self, bearing_geometry: Optional[Dict] = None):
        self.bearing_geometry = bearing_geometry or {
            'ball_diameter': 7.94,      # mm
            'pitch_diameter': 39.04,    # mm
            'num_balls': 9,
            'contact_angle': 0          # degrees
        }
        
        # Calculate theoretical fault orders
        self._calculate_fault_orders()
    
    def _calculate_fault_orders(self):
        """
        Calculate theoretical bearing fault orders
        
        Formulas from bearing kinematics:
        - BPFO (Ball Pass Frequency Outer): (n/2) * (1 - (d/D)*cos(φ))
        - BPFI (Ball Pass Frequency Inner): (n/2) * (1 + (d/D)*cos(φ))
        - BSF (Ball Spin Frequency): (D/2d) * (1 - (d/D)²*cos²(φ))
        - FTF (Fundamental Train Frequency): (1/2) * (1 - (d/D)*cos(φ))
        
        where:
        n = number of balls
        d = ball diameter
        D = pitch diameter
        φ = contact angle
        """
        n = self.bearing_geometry['num_balls']
        d = self.bearing_geometry['ball_diameter']
        D = self.bearing_geometry['pitch_diameter']
        phi = np.radians(self.bearing_geometry['contact_angle'])
        
        # Calculate orders (multiples of shaft speed)
        self.bpfo_order = (n / 2) * (1 - (d / D) * np.cos(phi))  # Outer race
        self.bpfi_order = (n / 2) * (1 + (d / D) * np.cos(phi))  # Inner race
        self.bsf_order = (D / (2 * d)) * (1 - ((d / D)**2) * (np.cos(phi)**2))  # Ball
        self.ftf_order = (1 / 2) * (1 - (d / D) * np.cos(phi))  # Cage
    
    def extract_features(self, signal_data: np.ndarray, speed_rpm: float, fs: float = 12000) -> Dict[str, float]:
        """
        Extract order-based features
        
        Parameters:
        -----------
        signal_data : np.ndarray
            Input vibration signal
        speed_rpm : float
            Shaft speed in RPM
        fs : float
            Sampling frequency in Hz
            
        Returns:
        --------
        dict : Dictionary of order features
        """
        features = {}
        
        # Convert RPM to Hz
        shaft_freq = speed_rpm / 60
        
        # Compute FFT
        fft_result = np.fft.fft(signal_data)
        freqs = np.fft.fftfreq(len(signal_data), 1/fs)
        
        # Take positive frequencies
        positive_idx = freqs > 0
        freqs = freqs[positive_idx]
        magnitude = np.abs(fft_result[positive_idx])
        
        # Calculate expected fault frequencies
        bpfo_freq = self.bpfo_order * shaft_freq
        bpfi_freq = self.bpfi_order * shaft_freq
        bsf_freq = self.bsf_order * shaft_freq
        ftf_freq = self.ftf_order * shaft_freq
        
        # Extract amplitude at each fault frequency (with tolerance)
        tolerance = 2  # Hz
        
        def get_amplitude_at_freq(target_freq):
            """Get maximum amplitude near target frequency"""
            mask = (freqs >= target_freq - tolerance) & (freqs <= target_freq + tolerance)
            if np.any(mask):
                return np.max(magnitude[mask])
            return 0.0
        
        # Amplitudes at fault frequencies
        features['bpfo_amplitude'] = get_amplitude_at_freq(bpfo_freq)
        features['bpfi_amplitude'] = get_amplitude_at_freq(bpfi_freq)
        features['bsf_amplitude'] = get_amplitude_at_freq(bsf_freq)
        features['ftf_amplitude'] = get_amplitude_at_freq(ftf_freq)
        
        # Ratios to shaft frequency amplitude
        shaft_amplitude = get_amplitude_at_freq(shaft_freq)
        if shaft_amplitude > 0:
            features['bpfo_ratio'] = features['bpfo_amplitude'] / shaft_amplitude
            features['bpfi_ratio'] = features['bpfi_amplitude'] / shaft_amplitude
            features['bsf_ratio'] = features['bsf_amplitude'] / shaft_amplitude
            features['ftf_ratio'] = features['ftf_amplitude'] / shaft_amplitude
        else:
            features['bpfo_ratio'] = 0.0
            features['bpfi_ratio'] = 0.0
            features['bsf_ratio'] = 0.0
            features['ftf_ratio'] = 0.0
        
        # Store theoretical orders for reference
        features['bpfo_order'] = self.bpfo_order
        features['bpfi_order'] = self.bpfi_order
        features['bsf_order'] = self.bsf_order
        features['ftf_order'] = self.ftf_order
        
        # Store shaft speed for reference
        features['shaft_speed_rpm'] = speed_rpm
        features['shaft_freq_hz'] = shaft_freq
        
        return features


def extract_all_advanced_features(signal_data: np.ndarray, 
                                   fs: float = 12000, 
                                   speed_rpm: Optional[float] = None) -> Dict[str, float]:
    """
    Extract all advanced features from a signal
    
    This is a convenience function that combines all feature extractors.
    
    Parameters:
    -----------
    signal_data : np.ndarray
        Input vibration signal
    fs : float
        Sampling frequency in Hz
    speed_rpm : float, optional
        Shaft speed in RPM (required for order tracking)
        
    Returns:
    --------
    dict : Dictionary containing all advanced features
    
    Usage Example:
    --------------
    >>> signal = np.random.randn(10000)  # Example signal
    >>> features = extract_all_advanced_features(signal, fs=12000, speed_rpm=1800)
    >>> print(f"Total features extracted: {len(features)}")
    """
    all_features = {}
    
    # 1. Wavelet features
    wavelet_extractor = WaveletFeatureExtractor(wavelet='db4', level=5)
    wavelet_features = wavelet_extractor.extract_features(signal_data)
    all_features.update(wavelet_features)
    
    # 2. Spectral features
    spectral_extractor = SpectralFeatureExtractor(fs=fs)
    spectral_features = spectral_extractor.extract_features(signal_data)
    all_features.update(spectral_features)
    
    # 3. Envelope spectrum features
    envelope_extractor = EnvelopeSpectrumExtractor(fs=fs)
    envelope_features = envelope_extractor.extract_features(signal_data)
    all_features.update(envelope_features)
    
    # 4. Order tracking features (if speed is provided)
    if speed_rpm is not None:
        order_extractor = OrderTrackingExtractor()
        order_features = order_extractor.extract_features(signal_data, speed_rpm, fs)
        all_features.update(order_features)
    
    return all_features


if __name__ == "__main__":
    """
    Test the advanced feature extractors
    """
    print("Testing Advanced Feature Extractors...")
    print("=" * 60)
    
    # Generate synthetic signal with fault signature
    fs = 12000  # 12 kHz sampling
    t = np.linspace(0, 1, fs)
    
    # Healthy signal: Low amplitude noise
    healthy_signal = 0.1 * np.random.randn(fs)
    
    # Faulty signal: Noise + periodic impacts (simulating bearing fault)
    fault_freq = 100  # Hz (simulated fault frequency)
    fault_signal = 0.1 * np.random.randn(fs) + 0.5 * np.sin(2 * np.pi * fault_freq * t)
    
    # Add impulsive component (characteristic of bearing faults)
    impact_times = np.arange(0, 1, 1/fault_freq)
    for impact_time in impact_times:
        impact_idx = int(impact_time * fs)
        if impact_idx < len(fault_signal):
            fault_signal[impact_idx] += 2.0
    
    # Extract features from both signals
    print("\n1. Testing Wavelet Features:")
    print("-" * 60)
    wavelet_ext = WaveletFeatureExtractor()
    healthy_wavelet = wavelet_ext.extract_features(healthy_signal)
    faulty_wavelet = wavelet_ext.extract_features(fault_signal)
    print(f"Healthy signal - Wavelet energy (level_1): {healthy_wavelet['wavelet_energy_level_1']:.4f}")
    print(f"Faulty signal - Wavelet energy (level_1): {faulty_wavelet['wavelet_energy_level_1']:.4f}")
    
    print("\n2. Testing Spectral Features:")
    print("-" * 60)
    spectral_ext = SpectralFeatureExtractor(fs=fs)
    healthy_spectral = spectral_ext.extract_features(healthy_signal)
    faulty_spectral = spectral_ext.extract_features(fault_signal)
    print(f"Healthy signal - Spectral centroid: {healthy_spectral['spectral_centroid']:.2f} Hz")
    print(f"Faulty signal - Spectral centroid: {faulty_spectral['spectral_centroid']:.2f} Hz")
    print(f"Healthy signal - Peak frequency: {healthy_spectral['peak_frequency']:.2f} Hz")
    print(f"Faulty signal - Peak frequency: {faulty_spectral['peak_frequency']:.2f} Hz")
    
    print("\n3. Testing Envelope Spectrum:")
    print("-" * 60)
    envelope_ext = EnvelopeSpectrumExtractor(fs=fs)
    healthy_envelope = envelope_ext.extract_features(healthy_signal)
    faulty_envelope = envelope_ext.extract_features(fault_signal)
    print(f"Healthy signal - Envelope kurtosis: {healthy_envelope['envelope_kurtosis']:.4f}")
    print(f"Faulty signal - Envelope kurtosis: {faulty_envelope['envelope_kurtosis']:.4f}")
    
    print("\n4. Testing Order Tracking:")
    print("-" * 60)
    order_ext = OrderTrackingExtractor()
    speed = 1800  # RPM
    order_features = order_ext.extract_features(fault_signal, speed, fs)
    print(f"Shaft speed: {speed} RPM ({speed/60:.2f} Hz)")
    print(f"BPFI order: {order_features['bpfi_order']:.2f}× shaft speed")
    print(f"BPFO order: {order_features['bpfo_order']:.2f}× shaft speed")
    print(f"BPFI amplitude: {order_features['bpfi_amplitude']:.4f}")
    
    print("\n5. Testing Combined Feature Extraction:")
    print("-" * 60)
    all_features = extract_all_advanced_features(fault_signal, fs=fs, speed_rpm=1800)
    print(f"Total features extracted: {len(all_features)}")
    print(f"Feature categories:")
    print(f"  - Wavelet features: {sum(1 for k in all_features if 'wavelet' in k)}")
    print(f"  - Spectral features: {sum(1 for k in all_features if 'spectral' in k)}")
    print(f"  - Envelope features: {sum(1 for k in all_features if 'envelope' in k)}")
    print(f"  - Order features: {sum(1 for k in all_features if any(x in k for x in ['bpfo', 'bpfi', 'bsf', 'ftf', 'shaft']))}")
    
    print("\n" + "=" * 60)
    print("Advanced Feature Extraction Module - Ready for Use!")
    print("=" * 60)
