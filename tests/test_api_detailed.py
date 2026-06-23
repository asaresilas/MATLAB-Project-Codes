"""
Comprehensive API Test with Detailed Error Reporting
"""
import requests
import numpy as np
import traceback

API_URL = "http://localhost:8000"

print("="*70)
print("COMPREHENSIVE API TEST")
print("="*70)

# Test 1: Health Check
print("\n[TEST 1] Health Check")
print("-"*70)
try:
    r = requests.get(f"{API_URL}/health", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    print("RESULT: PASS" if r.status_code == 200 else "RESULT: FAIL")
except Exception as e:
    print(f"RESULT: FAIL - {e}")

# Test 2: List Models
print("\n[TEST 2] List Loaded Models")
print("-"*70)
try:
    r = requests.get(f"{API_URL}/api/v1/models", timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Loaded Models: {data['loaded_models']}")
        print(f"Total: {len(data['loaded_models'])}/5")
        print("RESULT: PASS")
    else:
        print(f"Response: {r.text}")
        print("RESULT: FAIL")
except Exception as e:
    print(f"RESULT: FAIL - {e}")

# Test 3: Authentication (Detailed)
print("\n[TEST 3] Authentication (Detailed)")
print("-"*70)
try:
    print("Attempting login with admin/<ADMIN_PASSWORD env var>...")
    r = requests.post(
        f"{API_URL}/api/v1/auth/token",
        data={'username': 'admin', 'password': 'admin123'},
        timeout=10
    )
    
    print(f"Status Code: {r.status_code}")
    print(f"Headers: {dict(r.headers)}")
    
    if r.status_code == 200:
        token_data = r.json()
        token = token_data['access_token']
        print(f"SUCCESS! Token received:")
        print(f"  Token (first 30 chars): {token[:30]}...")
        print(f"  Expires in: {token_data.get('expires_in', 'N/A')} seconds")
        print("RESULT: PASS")
    else:
        print(f"FAILED!")
        print(f"Response Text: {r.text}")
        print(f"Response JSON: {r.json() if r.headers.get('content-type') == 'application/json' else 'Not JSON'}")
        print("RESULT: FAIL")
        token = None
        
except Exception as e:
    print(f"RESULT: FAIL - Exception occurred")
    print(f"Error: {e}")
    print(f"Traceback:\n{traceback.format_exc()}")
    token = None

# Test 4: Comprehensive Diagnosis (if authenticated)
if token:
    print("\n[TEST 4] Comprehensive Diagnosis")
    print("-"*70)
    try:
        print("Generating test vibration signal...")
        vibration = np.random.randn(12000).tolist()
        
        print("Sending diagnosis request...")
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.post(
            f"{API_URL}/api/v1/diagnose/comprehensive",
            headers=headers,
            json={
                'vibration_signal': vibration,
                'temperature': 65.0,
                'speed': 1750
            },
            timeout=60
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            print(f"\n=== DIAGNOSIS RESULTS ===")
            print(f"RUL: {result['rul_hours']:.1f} hours")
            print(f"Confidence: {result['rul_confidence']:.1%}")
            print(f"Overall Health: {result['overall_health']}")
            print(f"Action: {result['priority_action']}")
            
            if result['fault_locations']:
                print(f"\nDetected Faults ({len(result['fault_locations'])}):")
                for i, fault in enumerate(result['fault_locations'], 1):
                    print(f"  {i}. {fault['component']}: {fault['fault_type']}")
                    print(f"     Severity: {fault['severity']}, Confidence: {fault['confidence']:.1%}")
            
            print("\nRESULT: PASS - System fully operational!")
        else:
            print(f"Response: {r.text}")
            print("RESULT: FAIL")
            
    except Exception as e:
        print(f"RESULT: FAIL - {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
else:
    print("\n[TEST 4] Comprehensive Diagnosis")
    print("-"*70)
    print("SKIPPED - Authentication failed")

print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("\nIf authentication failed, check server logs for detailed error messages.")
print("Server is running on: http://localhost:8000")
