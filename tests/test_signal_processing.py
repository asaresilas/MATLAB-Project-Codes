"""
Unit Tests — src/features/signal_processing.py
================================================
Tests every public function in the signal processing module WITHOUT
hitting the live server. These are pure Python / NumPy unit tests.

Run:
    python -m pytest tests/test_signal_processing.py -v
"""

import sys
import os
import pytest
import numpy as np

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.features.signal_processing import (
    compute_fft,
    extract_time_features,
    envelope_spectrum,
    extract_combined_features,
    extract_induction_features,
    extract_nasa_features,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────

FS = 12_000   # Sampling frequency used throughout tests

@pytest.fixture
def pure_sine():
    """Single 100 Hz sine wave — deterministic, no randomness."""
    t = np.linspace(0, 1, FS, endpoint=False)
    return np.sin(2 * np.pi * 100 * t)

@pytest.fixture
def white_noise():
    """Reproducible Gaussian white noise."""
    rng = np.random.default_rng(42)
    return rng.normal(0, 0.1, FS)

@pytest.fixture
def impulsive_signal(white_noise):
    """White noise + periodic impulses at 100 Hz — simulates bearing fault."""
    sig = white_noise.copy()
    for i in range(0, FS, FS // 100):
        sig[i] += 3.0
    return sig

@pytest.fixture
def zero_signal():
    return np.zeros(1024)


# ─── compute_fft ─────────────────────────────────────────────────────────────

class TestComputeFFT:
    def test_returns_two_arrays(self, pure_sine):
        freqs, mags = compute_fft(pure_sine, FS)
        assert isinstance(freqs, np.ndarray)
        assert isinstance(mags, np.ndarray)

    def test_output_length_is_half_input(self, pure_sine):
        freqs, mags = compute_fft(pure_sine, FS)
        assert len(freqs) == len(pure_sine) // 2
        assert len(mags) == len(freqs)

    def test_peak_at_correct_frequency(self, pure_sine):
        """100 Hz sine wave must have its FFT peak at 100 Hz ± 1 bin."""
        freqs, mags = compute_fft(pure_sine, FS)
        peak_freq = freqs[np.argmax(mags)]
        assert abs(peak_freq - 100.0) < 2.0, f"Expected ~100 Hz, got {peak_freq:.2f} Hz"

    def test_frequencies_are_positive(self, pure_sine):
        freqs, _ = compute_fft(pure_sine, FS)
        assert np.all(freqs >= 0)

    def test_magnitudes_are_non_negative(self, pure_sine):
        _, mags = compute_fft(pure_sine, FS)
        assert np.all(mags >= 0)

    def test_dc_signal(self):
        """A pure DC signal should have all energy at 0 Hz."""
        dc = np.ones(1024)
        freqs, mags = compute_fft(dc, FS)
        assert mags[0] > mags[1:].max(), "DC signal peak should be at 0 Hz"


# ─── extract_time_features ───────────────────────────────────────────────────

class TestExtractTimeFeatures:
    EXPECTED_KEYS = {"rms", "mean", "std", "max", "min", "kurtosis", "skewness"}

    def test_returns_all_keys(self, pure_sine):
        features = extract_time_features(pure_sine)
        assert self.EXPECTED_KEYS == set(features.keys())

    def test_rms_of_unit_sine(self, pure_sine):
        """RMS of sin(x) = 1/√2 ≈ 0.7071."""
        features = extract_time_features(pure_sine)
        assert abs(features["rms"] - 1 / np.sqrt(2)) < 0.01

    def test_mean_of_sine_near_zero(self, pure_sine):
        features = extract_time_features(pure_sine)
        assert abs(features["mean"]) < 0.01

    def test_gaussian_kurtosis_near_3(self, white_noise):
        """Normal distribution kurtosis (Pearson) ≈ 3."""
        features = extract_time_features(white_noise)
        assert 2.0 < features["kurtosis"] < 5.0, (
            f"Gaussian kurtosis expected ~3, got {features['kurtosis']:.2f}"
        )

    def test_impulsive_kurtosis_higher_than_noise(self, white_noise, impulsive_signal):
        """Impulsive bearing-fault signal has higher kurtosis than white noise."""
        k_noise = extract_time_features(white_noise)["kurtosis"]
        k_fault = extract_time_features(impulsive_signal)["kurtosis"]
        assert k_fault > k_noise, (
            f"Fault kurtosis ({k_fault:.2f}) should exceed noise kurtosis ({k_noise:.2f})"
        )

    def test_zero_signal_no_division_error(self, zero_signal):
        """Zero signal must not raise ZeroDivisionError."""
        features = extract_time_features(zero_signal)
        assert features["rms"] == pytest.approx(0.0)

    def test_all_values_are_float(self, pure_sine):
        features = extract_time_features(pure_sine)
        for k, v in features.items():
            assert isinstance(float(v), float), f"Feature {k} is not numeric"

    def test_max_gte_min(self, pure_sine):
        features = extract_time_features(pure_sine)
        assert features["max"] >= features["min"]


# ─── envelope_spectrum ────────────────────────────────────────────────────────

class TestEnvelopeSpectrum:
    def test_returns_two_arrays(self, pure_sine):
        freqs, mags = envelope_spectrum(pure_sine, FS)
        assert isinstance(freqs, np.ndarray)
        assert isinstance(mags, np.ndarray)
        assert len(freqs) == len(mags)

    def test_magnitudes_non_negative(self, pure_sine):
        _, mags = envelope_spectrum(pure_sine, FS)
        assert np.all(mags >= 0)

    def test_detects_modulation_frequency(self):
        """
        Simulate bearing fault: 5 kHz resonance modulated at 100 Hz.
        The envelope spectrum should have its largest non-DC peak at ~100 Hz.
        We skip the DC bin (index 0) because the mean of the envelope dominates.
        """
        t = np.linspace(0, 1, FS, endpoint=False)
        carrier = np.sin(2 * np.pi * 5000 * t)
        modulation = 1 + 0.5 * np.sin(2 * np.pi * 100 * t)
        signal = carrier * modulation
        freqs, mags = envelope_spectrum(signal, FS)
        # Search for peak in 50–500 Hz band (excluding DC at index 0)
        band_mask = (freqs >= 50) & (freqs <= 500)
        if not np.any(band_mask):
            pytest.skip("No frequency bins in 50-500 Hz band")
        peak_freq = freqs[band_mask][np.argmax(mags[band_mask])]
        assert abs(peak_freq - 100.0) < 5.0, (
            f"Envelope peak expected ~100 Hz in 50-500 Hz band, got {peak_freq:.2f} Hz"
        )


# ─── extract_combined_features ───────────────────────────────────────────────

class TestExtractCombinedFeatures:
    REQUIRED_KEYS = {
        "rms", "mean", "std", "max", "min", "kurtosis", "skewness",
        "peak_frequency", "peak_amplitude",
        "low_freq_energy", "mid_freq_energy", "high_freq_energy",
        "envelope_peak_freq", "envelope_peak_amplitude",
    }

    def test_returns_all_required_keys(self, pure_sine):
        features = extract_combined_features(pure_sine, FS)
        missing = self.REQUIRED_KEYS - set(features.keys())
        assert not missing, f"Missing feature keys: {missing}"

    def test_all_values_finite(self, pure_sine):
        features = extract_combined_features(pure_sine, FS)
        for k, v in features.items():
            assert np.isfinite(v), f"Feature {k} = {v} is not finite"

    def test_default_fs_works(self, pure_sine):
        """Should not raise when called without explicit fs."""
        features = extract_combined_features(pure_sine)
        assert len(features) >= 14


# ─── extract_induction_features ──────────────────────────────────────────────

class TestExtractInductionFeatures:
    def test_returns_13_features(self, pure_sine):
        features = extract_induction_features(pure_sine)
        assert len(features) == 13, f"Expected 13 features, got {len(features)}"

    def test_returns_list_of_floats(self, pure_sine):
        features = extract_induction_features(pure_sine)
        assert all(isinstance(float(v), float) for v in features)

    def test_all_values_finite(self, pure_sine):
        features = extract_induction_features(pure_sine)
        assert all(np.isfinite(v) for v in features), "Some induction features are NaN/Inf"

    def test_rms_matches_numpy(self, pure_sine):
        features = extract_induction_features(pure_sine)
        rms = features[0]  # index 0 is RMS
        expected_rms = np.sqrt(np.mean(pure_sine ** 2))
        assert abs(rms - expected_rms) < 1e-6

    def test_works_with_2048_samples(self):
        """Induction motor model requires 2048-sample input."""
        rng = np.random.default_rng(0)
        sig = rng.normal(0, 0.5, 2048)
        features = extract_induction_features(sig)
        assert len(features) == 13


# ─── extract_nasa_features ────────────────────────────────────────────────────

class TestExtractNASAFeatures:
    EXPECTED_KEYS = {
        "rms", "mean", "std", "max", "min",
        "kurtosis", "skewness", "peak_to_peak", "crest_factor"
    }

    def test_returns_9_keys(self, pure_sine):
        features = extract_nasa_features(pure_sine)
        assert set(features.keys()) == self.EXPECTED_KEYS

    def test_peak_to_peak_correct(self, pure_sine):
        features = extract_nasa_features(pure_sine)
        expected = np.max(pure_sine) - np.min(pure_sine)
        assert abs(features["peak_to_peak"] - expected) < 1e-6

    def test_crest_factor_unit_sine(self, pure_sine):
        """Crest factor of sin(x) = peak / rms = 1 / (1/√2) = √2 ≈ 1.414."""
        features = extract_nasa_features(pure_sine)
        assert abs(features["crest_factor"] - np.sqrt(2)) < 0.05

    def test_zero_signal_no_crash(self, zero_signal):
        """Zero-std signal must return 0 for shape stats without error."""
        features = extract_nasa_features(zero_signal)
        assert features["kurtosis"] == 0
        assert features["skewness"] == 0

    def test_all_values_finite(self, white_noise):
        features = extract_nasa_features(white_noise)
        for k, v in features.items():
            assert np.isfinite(v), f"NASA feature {k} = {v} is not finite"

    def test_kurtosis_pearson_formula(self):
        """
        Kurtosis uses the Pearson formula (normal=3), NOT excess kurtosis (normal=0).
        Verify a normal sample gives kurtosis near 3.
        """
        rng = np.random.default_rng(99)
        signal = rng.normal(0, 1, 50_000)
        features = extract_nasa_features(signal)
        assert 2.5 < features["kurtosis"] < 3.5, (
            f"Pearson kurtosis expected ~3 for normal data, got {features['kurtosis']:.3f}"
        )
