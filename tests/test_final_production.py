"""Final System Test - All Models"""
import requests
import numpy as npimport os

API_URL = "http://localhost:8000"

print("="*70)
print("FINAL PRODUCTION SYSTEM TEST")
print("="*70)

# Test 1: Health
print("\n[1] Health Check")
r = requests.get(f"{API_URL}/health")
print(f"Status: {r.status_code} - {'PASS' if r.status_code == 200 else 'FAIL'}")

# Test 2: Models Loaded
print("\n[2] Check Loaded Models")
r = requests.get(f"{API_URL}/api/v1/models")
if r.status_code == 200:
    models = r.json()['loaded_models']
    print(f"Loaded Models: {models}")
    print(f"Count: {len(models)}/5")
    print("PASS" if len(models) == 5 else "FAIL")

# Test 3: Auth (try both passwords)
print("\n[3] Authentication Test")
test_pwd = os.getenv("ADMIN_PASSWORD", "secure_default_pass_12345")
for pwd in [test_pwd, os.getenv('ADMIN_PASSWORD', '')]:
    try:
        r = requests.post(
            f"{API_URL}/api/v1/auth/token",
            data={'username': os.getenv('ADMIN_USERNAME', 'admin'), 'password': pwd}
        )
        if r.status_code == 200:
            token = r.json()['access_token']
            print(f"SUCCESS with password: {pwd}")
            print(f"Token: {token[:30]}...")
            break
        else:
            print(f"Failed with '{pwd}': {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("FAIL - Could not authenticate")
    token = None

# Test 4: Comprehensive Diagnosis
if token:
    print("\n[4] Comprehensive Diagnosis")
    vibration = np.random.randn(12000).tolist()
    
    r = requests.post(
        f"{API_URL}/api/v1/diagnose/comprehensive",
        headers={'Authorization': f'Bearer {token}'},
        json={
            'vibration_signal': vibration,
            'temperature': 65.0,
            'speed': 1750
        },
        timeout=60
    )
    
    if r.status_code == 200:
        result = r.json()
        print(f"RUL: {result['rul_hours']:.1f} hours")
        print(f"Health: {result['overall_health']}")
        print(f"Faults: {len(result['fault_locations'])}")
        print("PASS - System fully operational!")
    else:
        print(f"FAIL - Status: {r.status_code}")

print("\n" + "="*70)
