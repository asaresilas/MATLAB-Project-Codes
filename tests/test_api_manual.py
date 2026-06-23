"""
Simple API Test - Manual Server Testing

This script tests the API endpoints assuming the server is already running.
Run this AFTER starting the server manually with:
    cd backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import requests
import numpy as np
import json
import time

API_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_list_models():
    """Test models listing"""
    print("\n" + "="*70)
    print("TEST 2: List Models")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/v1/models", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Loaded models: {data['loaded_models']}")
            print(f"Configs: {len(data['configs'])} datasets")
            return 'NASA' in data['loaded_models']
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_nasa_raw_signal():
    """Test NASA prediction with raw signal"""
    print("\n" + "="*70)
    print("TEST 3: NASA Prediction (Raw Signal)")
    print("="*70)
    
    # Generate test signal
    fs = 12000
    t = np.linspace(0, 1, fs)
    vibration = 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(fs)
    
    payload = {"signal": vibration.tolist()}
    
    print(f"Sending {len(vibration)} samples...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/predict/nasa",
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"RUL Prediction: {data['rul']:.2f} hours")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    print("="*70)
    print("API Test (Manual Server)")
    print("="*70)
    print("\nMake sure the server is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("\nWaiting 3 seconds for you to confirm...")
    time.sleep(3)
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("List Models", test_list_models()))
    results.append(("NASA Prediction", test_nasa_raw_signal()))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name:<30} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
