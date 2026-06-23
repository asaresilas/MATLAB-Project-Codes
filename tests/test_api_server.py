"""
API Server Test - End-to-End Verification

This script starts the FastAPI server and sends real HTTP requests
to verify the NASA RUL prediction endpoint works correctly.

Usage:
    python tests/test_api_server.py
"""

import sys
import os
import time
import requests
import numpy as np
import json
import subprocess
import signal

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

API_URL = "http://localhost:8000"
SERVER_PROCESS = None

def start_server():
    """Start the FastAPI server in background"""
    global SERVER_PROCESS
    
    print("Starting FastAPI server...")
    backend_dir = os.path.join(project_root, 'backend')
    
    # Start uvicorn server
    SERVER_PROCESS = subprocess.Popen(
        ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to start", end="")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/health", timeout=1)
            if response.status_code == 200:
                print(" ✓")
                print(f"Server is running at {API_URL}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print(" ✗")
    print("Failed to start server")
    return False

def stop_server():
    """Stop the FastAPI server"""
    global SERVER_PROCESS
    
    if SERVER_PROCESS:
        print("\nStopping server...")
        SERVER_PROCESS.send_signal(signal.SIGTERM)
        SERVER_PROCESS.wait(timeout=5)
        print("✓ Server stopped")

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json()['status'] == 'healthy':
            print("✓ PASS: Health check successful")
            return True
        else:
            print("✗ FAIL: Unexpected response")
            return False
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_list_models():
    """Test the models listing endpoint"""
    print("\n" + "="*70)
    print("TEST 2: List Models")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/v1/models")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Loaded Models: {data['loaded_models']}")
            print(f"Number of configs: {len(data['configs'])}")
            
            if 'NASA' in data['loaded_models']:
                print("✓ PASS: NASA model is loaded")
                return True
            else:
                print("⚠ WARNING: NASA model not loaded")
                print("This may be expected if models failed to load during startup")
                return False
        else:
            print("✗ FAIL: Unexpected status code")
            return False
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_nasa_prediction_raw_signal():
    """Test NASA prediction with raw vibration signal"""
    print("\n" + "="*70)
    print("TEST 3: NASA Prediction (Raw Signal)")
    print("="*70)
    
    # Generate test signal
    fs = 12000
    t = np.linspace(0, 1, fs)
    vibration = 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(fs)
    
    payload = {
        "signal": vibration.tolist()
    }
    
    print(f"Sending signal with {len(vibration)} samples...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/predict/nasa",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if 'rul' in data and isinstance(data['rul'], (int, float)):
                print(f"\n✓ PASS: Predicted RUL = {data['rul']:.2f} hours")
                return True
            else:
                print("✗ FAIL: Invalid response format")
                return False
                
        elif response.status_code == 503:
            print("⚠ WARNING: Model not loaded")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"✗ FAIL: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_nasa_prediction_preprocessed():
    """Test NASA prediction with pre-processed features"""
    print("\n" + "="*70)
    print("TEST 4: NASA Prediction (Pre-processed Features)")
    print("="*70)
    
    # Create dummy feature sequence (10 timesteps × 36 features)
    # In reality, this would come from your feature extraction pipeline
    feature_sequence = np.random.randn(10, 36).tolist()
    
    payload = {
        "data": feature_sequence
    }
    
    print(f"Sending pre-processed features (shape: 10 × 36)...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/predict/nasa",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if 'rul' in data and isinstance(data['rul'], (int, float)):
                print(f"\n✓ PASS: Predicted RUL = {data['rul']:.2f} hours")
                return True
            else:
                print("✗ FAIL: Invalid response format")
                return False
                
        elif response.status_code == 503:
            print("⚠ WARNING: Model not loaded")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"✗ FAIL: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def main():
    print("="*70)
    print("FastAPI Server End-to-End Test")
    print("="*70)
    
    # Start server
    if not start_server():
        print("\n✗ Cannot proceed without server")
        return
    
    try:
        # Run tests
        results = []
        results.append(("Health Check", test_health_check()))
        results.append(("List Models", test_list_models()))
        results.append(("NASA Prediction (Raw)", test_nasa_prediction_raw_signal()))
        results.append(("NASA Prediction (Preprocessed)", test_nasa_prediction_preprocessed()))
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        for test_name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{test_name:<40} {status}")
        
        total = len(results)
        passed = sum(results, key=lambda x: x[1])
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        elif passed > 0:
            print("\n⚠ Some tests failed - check logs above")
        else:
            print("\n✗ All tests failed - check server configuration")
            
    finally:
        # Always stop server
        stop_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        stop_server()
