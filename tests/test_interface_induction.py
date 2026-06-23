import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.interface import analyze_motor_data

def test_induction_interface():
    print("Testing Induction Motor Interface...")
    
    # Generate dummy signal (similar to what MATLAB would send)
    # 1 second of data at 10kHz
    fs = 10000
    t = np.linspace(0, 1, fs)
    
    # Simulate a "Damaged Ring" signal (based on my knowledge of what might trigger it, 
    # or just random noise to see if it runs)
    # The model uses FFT features, so let's add some frequency components.
    # Random noise
    signal = np.random.randn(fs) * 0.1
    # Simulate a realistic motor current/vibration signal rather than pure noise
    # Fundamental frequency (e.g., 60Hz mains), a harmonic (120Hz), and a simulated fault frequency (e.g., 175Hz)
    f_fundamental = 60.0
    f_harmonic = 120.0
    f_fault = 175.0
    signal = (np.sin(2 * np.pi * f_fundamental * t) + 
              0.5 * np.sin(2 * np.pi * f_harmonic * t) + 
              0.2 * np.sin(2 * np.pi * f_fault * t) + 
              np.random.randn(fs) * 0.05)  # Add realistic noise floor
    
    # Call analyze_motor_data
    print("Calling analyze_motor_data with dataset='induction'...")
    result = analyze_motor_data(
        vibration_signal=signal,
        current_signal=[], # Not used yet
        temperature=45.0,
        speed=1750.0,
        dataset='induction'
    )
    
    print("\nResult:")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print(f"RUL: {result['rul_hours']:.2f} hours")
    print(f"Recommendation: {result['recommendation']}")
    
    # Check features
    feats = result['features']
    print(f"\nFeatures extracted: {len(feats)}")
    print(f"Feature vector: {feats}")
    
    # Assertions for robust testing
    valid_statuses = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']
    assert result['status'] in valid_statuses, f"FAILURE: Unexpected status '{result['status']}'"
    assert 'rul_hours' in result, "FAILURE: Missing RUL estimation"
    assert 'confidence' in result, "FAILURE: Missing confidence score"
    
    print("\nSUCCESS: Valid status returned and assertions passed.")

if __name__ == "__main__":
    test_induction_interface()
