"""Simple API Test - No Unicode"""
import requests
import numpy as np

API_URL = "http://localhost:8000"

print("="*70)
print("SYSTEM VERIFICATION TEST")
print("="*70)

# Test 1: Health Check
print("\n[TEST 1] Health Check")
try:
    r = requests.get(f"{API_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    print("RESULT: PASS" if r.status_code == 200 else "RESULT: FAIL")
except Exception as e:
    print(f"RESULT: FAIL - {e}")

# Test 2: Authentication
print("\n[TEST 2] Authentication")
try:
    r = requests.post(
        f"{API_URL}/api/v1/auth/token",
        data={'username': 'admin', 'password': os.getenv('ADMIN_PASSWORD', '')}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        token = r.json()['access_token']
        print(f"Token received (first 20 chars): {token[:20]}...")
        print("RESULT: PASS")
    else:
        print(f"Response: {r.text}")
        print("RESULT: FAIL")
        token = None
except Exception as e:
    print(f"RESULT: FAIL - {e}")
    token = None

# Test 3: Comprehensive Diagnosis
if token:
    print("\n[TEST 3] Comprehensive Diagnosis")
    try:
        vibration = np.random.randn(12000).tolist()
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
            print(f"\nRUL: {result['rul_hours']:.1f} hours")
            print(f"Confidence: {result['rul_confidence']:.1%}")
            print(f"Health: {result['overall_health']}")
            print(f"Action: {result['priority_action']}")
            
            if result['fault_locations']:
                print(f"\nFaults Detected: {len(result['fault_locations'])}")
                for fault in result['fault_locations']:
                    print(f"  - {fault['component']}: {fault['fault_type']}")
            
            print("\nRESULT: PASS")
        else:
            print(f"Response: {r.text}")
            print("RESULT: FAIL")
            
    except Exception as e:
        print(f"RESULT: FAIL - {e}")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
