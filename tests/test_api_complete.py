"""
Complete API Test Script
Tests all endpoints with proper data formats
"""

import os
import requests
import numpy as np
import json
from datetime import datetime

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def test_health():
    """Test 1: Health Check"""
    print_section("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("[PASS] Server is healthy")
            return True
        else:
            print("[FAIL] Server not responding properly")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_models():
    """Test 2: List Loaded Models"""
    print_section("TEST 2: List Loaded Models")
    
    try:
        response = requests.get(f"{API_URL}/api/v1/models", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data['loaded_models']
            print(f"Loaded Models: {models}")
            print(f"Total: {len(models)}/5")
            
            if len(models) == 5:
                print("✅ PASS - All 5 models loaded")
                return True
            else:
                print(f"⚠️  WARNING - Only {len(models)} models loaded")
                return False
        else:
            print("❌ FAIL - Could not retrieve models")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_authentication():
    """Test 3: Authentication"""
    print_section("TEST 3: Authentication")
    
    try:
        print(f"Attempting login with {USERNAME}/{PASSWORD}...")
        response = requests.post(
            f"{API_URL}/api/v1/auth/token",
            data={'username': USERNAME, 'password': PASSWORD},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['access_token']
            expires = token_data['expires_in']
            
            print(f"✅ PASS - Authentication successful")
            print(f"Token (first 30 chars): {token[:30]}...")
            print(f"Expires in: {expires} seconds ({expires//60} minutes)")
            return token
        else:
            print(f"❌ FAIL - Authentication failed")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return None

def test_user_info(token):
    """Test 4: Get User Info"""
    print_section("TEST 4: Get User Info")
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{API_URL}/api/v1/auth/me",
            headers=headers,
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"Username: {user['username']}")
            print(f"Email: {user.get('email', 'N/A')}")
            print(f"Full Name: {user.get('full_name', 'N/A')}")
            print("✅ PASS - User info retrieved")
            return True
        else:
            print(f"❌ FAIL - Could not get user info")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_comprehensive_diagnosis(token):
    """Test 5: Comprehensive Diagnosis with Proper Data"""
    print_section("TEST 5: Comprehensive Diagnosis")
    
    try:
        print("Generating test data...")
        print("  - Vibration signal: 12,000 samples")
        print("  - Current signal: 1,000 samples × 3 phases")
        
        # Generate proper test data
        vibration = np.random.randn(12000).tolist()
        current = np.random.randn(1000, 3).tolist()
        
        print("\nSending diagnosis request...")
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "-"*70)
            print("DIAGNOSTIC RESULTS")
            print("-"*70)
            
            # RUL
            print(f"\n🕐 REMAINING USEFUL LIFE")
            print(f"   Hours: {result['rul_hours']:.2f}")
            print(f"   Confidence: {result['rul_confidence']:.1%}")
            
            # Overall Health
            print(f"\n❤️  OVERALL HEALTH: {result['overall_health']}")
            print(f"⚠️  ACTION: {result['priority_action']}")
            
            # Faults
            if result['fault_locations']:
                print(f"\n🔍 DETECTED FAULTS ({len(result['fault_locations'])})")
                for i, fault in enumerate(result['fault_locations'], 1):
                    print(f"\n   {i}. {fault['component']}")
                    print(f"      Type: {fault['fault_type']}")
                    print(f"      Severity: {fault['severity']}")
                    print(f"      Confidence: {fault['confidence']:.1%}")
            else:
                print("\n✅ No faults detected - Equipment is healthy")
            
            # Detailed Analysis
            if result.get('bearing_analysis'):
                print(f"\n🔩 BEARING ANALYSIS")
                print(f"   Status: {result['bearing_analysis']['fault_type']}")
                print(f"   Confidence: {result['bearing_analysis']['confidence']:.1%}")
                if 'probabilities' in result['bearing_analysis']:
                    print(f"   Probabilities:")
                    for fault_type, prob in result['bearing_analysis']['probabilities'].items():
                        print(f"     - {fault_type}: {prob:.1%}")
            
            if result.get('motor_analysis'):
                print(f"\n⚙️  MOTOR ANALYSIS")
                print(f"   Status: {result['motor_analysis']['status']}")
                print(f"   Confidence: {result['motor_analysis']['confidence']:.1%}")
            
            if result.get('electrical_analysis'):
                print(f"\n⚡ ELECTRICAL ANALYSIS")
                print(f"   Status: {result['electrical_analysis']['status']}")
                print(f"   Confidence: {result['electrical_analysis']['confidence']:.1%}")
            
            print("\n" + "-"*70)
            print("✅ PASS - Comprehensive diagnosis completed successfully")
            return True
        else:
            print(f"❌ FAIL - Diagnosis failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return False

def save_results(results):
    """Save test results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"api_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {filename}")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" COMPREHENSIVE API TEST SUITE")
    print(" " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'api_url': API_URL,
        'tests': {}
    }
    
    # Test 1: Health Check
    results['tests']['health'] = test_health()
    
    # Test 2: Models
    results['tests']['models'] = test_models()
    
    # Test 3: Authentication
    token = test_authentication()
    results['tests']['authentication'] = token is not None
    
    if token:
        # Test 4: User Info
        results['tests']['user_info'] = test_user_info(token)
        
        # Test 5: Comprehensive Diagnosis
        results['tests']['diagnosis'] = test_comprehensive_diagnosis(token)
    else:
        print("\n⚠️  Skipping authenticated tests - authentication failed")
        results['tests']['user_info'] = False
        results['tests']['diagnosis'] = False
    
    # Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results['tests'])
    passed_tests = sum(1 for v in results['tests'].values() if v)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, passed in results['tests'].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:20s} {status}")
    
    # Save results
    save_results(results)
    
    # Final verdict
    print("\n" + "="*70)
    if passed_tests == total_tests:
        print(" 🎉 ALL TESTS PASSED - API IS FULLY OPERATIONAL!")
    elif passed_tests >= total_tests * 0.8:
        print(" ⚠️  MOST TESTS PASSED - API IS MOSTLY OPERATIONAL")
    else:
        print(" ❌ MULTIPLE TESTS FAILED - API NEEDS ATTENTION")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
