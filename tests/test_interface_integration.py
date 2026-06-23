import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.interface import analyze_motor_data

def test_interface():
    print("Testing Interface Integration...")
    print("=" * 60)
    
    # 1. Generate Dummy Data (Normal)
    # Normal signal: Low amplitude noise
    fs = 12000
    t = np.linspace(0, 1, fs)
    normal_vib = 0.05 * np.random.randn(fs)
    current = np.random.randn(fs)
    temp = 45.0
    speed = 1750.0
    
    print("\nTest Case 1: Normal Operation")
    result_normal = analyze_motor_data(normal_vib, current, temp, speed)
    print(f"Status: {result_normal['status']}")
    print(f"Confidence: {result_normal['confidence']:.4f}")
    print(f"RUL: {result_normal['rul_hours']:.1f} hours")
    print(f"Recommendation: {result_normal['recommendation']}")
    
    # 2. Generate Dummy Data (Faulty - Inner Race)
    # Inner race fault often has impulsive impacts
    # We'll simulate high kurtosis and RMS
    faulty_vib = 0.1 * np.random.randn(fs)
    # Add impacts
    for i in range(0, fs, fs//100):
        if i < fs:
            faulty_vib[i] += 2.0
            
    print("\nTest Case 2: Faulty Operation (Simulated)")
    result_faulty = analyze_motor_data(faulty_vib, current, temp, speed)
    print(f"Status: {result_faulty['status']}")
    print(f"Confidence: {result_faulty['confidence']:.4f}")
    print(f"RUL: {result_faulty['rul_hours']:.1f} hours")
    print(f"Recommendation: {result_faulty['recommendation']}")
    
    # 3. High Temp Case
    print("\nTest Case 3: High Temperature")
    result_temp = analyze_motor_data(normal_vib, current, 85.0, speed)
    print(f"Status: {result_temp['status']}")
    print(f"RUL: {result_temp['rul_hours']:.1f} hours")
    print(f"Recommendation: {result_temp['recommendation']}")

    print("\n" + "=" * 60)
    print("Interface Test Completed.")

if __name__ == "__main__":
    test_interface()
