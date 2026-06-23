import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interface import analyze_motor_data, model_manager

def test_rul_prediction():
    print("Testing RUL Prediction Integration...")
    
    # 1. Generate dummy vibration data (1 second at 12kHz)
    # Simulate a signal with some noise and a fault frequency
    fs = 12000
    t = np.linspace(0, 1, fs)
    vibration = 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(fs)
    
    # 2. Call analyze_motor_data
    print("\nCalling analyze_motor_data...")
    try:
        result = analyze_motor_data(
            vibration_signal=vibration,
            current_signal=[], # Not used for NASA/CWRU
            temperature=45.0,
            speed=1750,
            dataset='nasa' # Use 'nasa' to trigger RUL logic if we add that switch, or just rely on default
        )
        
        print("\nResult:")
        print(f"Status: {result['status']}")
        print(f"RUL (Hours): {result['rul_hours']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Recommendation: {result['recommendation']}")
        
        # Check if RUL is valid
        if isinstance(result['rul_hours'], (int, float)) and result['rul_hours'] >= 0:
            print("\nSUCCESS: RUL returned a valid number.")
        else:
            print("\nFAILURE: RUL returned invalid value.")
            
        # Check if DL model was actually used
        if model_manager.rul_predictor is not None:
            print("Verified: DL Model (Bi-LSTM) is loaded.")
        else:
            print("Warning: DL Model is NOT loaded (using heuristic).")
            
    except Exception as e:
        print(f"\nFAILURE: Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rul_prediction()
