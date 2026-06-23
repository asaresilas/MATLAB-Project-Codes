"""
Simple API Test Script - No Unicode
Tests all endpoints with proper data formats
"""

import requests
import numpy as np
from datetime import datetime

API_URL = "http://localhost:8000"

print("="*70)
print("API TEST SUITE")
print("="*70)

# Test 1: Health Check
print("\n[TEST 1] Health Check")
try:
    r = requests.get(f"{API_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    print("Result: PASS" if r.status_code == 200 else "Result: FAIL")
except Exception as e:
    print(f"Result: FAIL - {e}")

# Test 2: Models
print("\n[TEST 2] List Models")
try:
    r = requests.get(f"{API_URL}/api/v1/models")
    if r.status_code == 200:
        models = r.json()['loaded_models']
        print(f"Models: {models}")
        print(f"Count: {len(models)}/5")
        print("Result: PASS")
    else:
        print("Result: FAIL")
except Exception as e:
    print(f"Result: FAIL - {e}")

# Test 3: Authentication
print("\n[TEST 3] Authentication")
try:
    r = requests.post(
        f"{API_URL}/api/v1/auth/token",
        data={'username': 'admin', 'password': os.getenv('ADMIN_PASSWORD', '')}
    )
    if r.status_code == 200:
        token = r.json()['access_token']
        print(f"Token: {token[:30]}...")
        print(f"Expires: {r.json()['expires_in']} seconds")
        print("Result: PASS")
    else:
        print(f"Result: FAIL - {r.status_code}")
        token = None
except Exception as e:
    print(f"Result: FAIL - {e}")
    token = None

# Test 4: Comprehensive Diagnosis
if token:
    print("\n[TEST 4] Comprehensive Diagnosis")
    try:
        print("Generating data: 12,000 vibration + 1,000x3 current samples...")
        
        vibration = np.random.randn(12000).tolist()
        current = np.random.randn(1000, 3).tolist()
        
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.post(
            f"{API_URL}/api/v1/diagnose/comprehensive",
            headers=headers,
            json={
                'vibration_signal': vibration,
                'current_signal': current,
                'temperature': 75.0,
                'speed': 1050
            },
            timeout=60
        )
        
        if r.status_code == 200:
            result = r.json()
            
            print("\n" + "-"*70)
            print("DIAGNOSTIC RESULTS")
            print("-"*70)
            print(f"\nRUL: {result['rul_hours']:.2f} hours")
            print(f"Confidence: {result['rul_confidence']:.1%}")
            print(f"Health: {result['overall_health']}")
            print(f"Action: {result['priority_action']}")
            
            if result['fault_locations']:
                print(f"\nFaults Detected: {len(result['fault_locations'])}")
                for fault in result['fault_locations']:
                    print(f"  - {fault['component']}: {fault['fault_type']} ({fault['severity']})")
            else:
                print("\nNo faults detected")
            
            if result.get('bearing_analysis'):
                print(f"\nBearing: {result['bearing_analysis']['fault_type']}")
            if result.get('motor_analysis'):
                print(f"Motor: {result['motor_analysis']['status']}")
            if result.get('electrical_analysis'):
                print(f"Electrical: {result['electrical_analysis']['status']}")
            
            print("-"*70)
            print("Result: PASS")
        else:
            print(f"Result: FAIL - Status {r.status_code}")
            print(f"Response: {r.text}")
    except Exception as e:
        print(f"Result: FAIL - {e}")
else:
    print("\n[TEST 4] Skipped - No authentication token")

# Test 5: Realistic Fault Signal (Synthetic)
if token:
    print("\n[TEST 5] Realistic Fault Signal (Synthetic)")
    
    def generate_synthetic_signal(n_samples=12000, condition='healthy'):
        t = np.linspace(0, 1, n_samples)
        # Base 60Hz signal
        signal = 0.5 * np.sin(2 * np.pi * 60 * t)
        
        if condition == 'faulty':
            # Add harmonics (120Hz, 180Hz) - typical of faults
            signal += 0.2 * np.sin(2 * np.pi * 120 * t)
            signal += 0.1 * np.sin(2 * np.pi * 180 * t)
            # Add impulsive noise (bearing clicks)
            noise = np.random.normal(0, 0.1, n_samples)
            impulses = np.random.choice([0, 2.0], size=n_samples, p=[0.995, 0.005])
            signal += noise + impulses
        else:
            # Healthy: just small noise
            noise = np.random.normal(0, 0.05, n_samples)
            signal += noise
            
        return signal.tolist()

    try:
        print("Generating synthetic FAULTY signal...")
        faulty_signal = generate_synthetic_signal(condition='faulty')
        current = np.random.randn(1000, 3).tolist() # Current doesn't matter for this test
        
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.post(
            f"{API_URL}/api/v1/diagnose/comprehensive",
            headers=headers,
            json={
                'vibration_signal': faulty_signal,
                'current_signal': current,
                'temperature': 75.0,
                'speed': 1050
            },
            timeout=60
        )
        
        if r.status_code == 200:
            result = r.json()
            print(f"RUL Confidence: {result['rul_confidence']:.1%}")
            # print(f"Fault Confidence: {result['confidence']:.1%}") # Key 'confidence' not in top-level output
            print(f"Status: {result['overall_health']}")
            
            if result['rul_confidence'] > 0.9:
                print("Result: PASS (High Confidence Achieved)")
            else:
                print(f"Result: WARNING (Confidence {result['rul_confidence']:.1%} < 90%)")
        else:
            print(f"Result: FAIL - Status {r.status_code}")
            
    except Exception as e:
        print(f"Result: FAIL - {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
