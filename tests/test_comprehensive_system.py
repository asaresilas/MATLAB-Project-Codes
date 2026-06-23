"""
Test Comprehensive Diagnostic System

This script tests the complete system with all 5 models integrated.
"""

import requests
import numpy as np
import json
from datetime import datetime

API_URL = "http://localhost:8001"

def test_complete_system():
    print("="*70)
    print("COMPREHENSIVE DIAGNOSTIC SYSTEM TEST")
    print("="*70)
    
    # Step 1: Authenticate
    print("\n[STEP 1] Authentication")
    print("-" * 70)
    
    try:
        auth_response = requests.post(
            f"{API_URL}/api/v1/auth/token",
            data={
                'username': 'admin',
                'password': os.getenv('ADMIN_PASSWORD', '')
            }
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()['access_token']
            print(f"✓ Authenticated successfully")
            print(f"  Token expires in: {auth_response.json()['expires_in']} seconds")
        else:
            print(f"✗ Authentication failed: {auth_response.text}")
            return
            
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return
    
    # Step 2: Test Comprehensive Diagnosis
    print("\n[STEP 2] Comprehensive Diagnosis")
    print("-" * 70)
    
    # Generate test data
    vibration_signal = np.random.randn(12000).tolist()
    current_signal = np.random.randn(1000, 3).tolist()
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'vibration_signal': vibration_signal,
        'current_signal': current_signal,
        'temperature': 65.0,
        'speed': 1750
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/diagnose/comprehensive",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✓ Diagnosis completed successfully\n")
            
            # Display results
            print("="*70)
            print("DIAGNOSTIC REPORT")
            print("="*70)
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # RUL
            print(f"REMAINING USEFUL LIFE: {result['rul_hours']:.1f} hours")
            print(f"Confidence: {result['rul_confidence']:.1%}\n")
            
            # Faults
            if result['fault_locations']:
                print("DETECTED FAULTS:")
                for i, fault in enumerate(result['fault_locations'], 1):
                    print(f"\n{i}. Component: {fault['component']}")
                    print(f"   Fault Type: {fault['fault_type']}")
                    print(f"   Severity: {fault['severity']}")
                    print(f"   Confidence: {fault['confidence']:.1%}")
            else:
                print("✓ No faults detected\n")
            
            # Overall assessment
            print(f"\nOVERALL HEALTH: {result['overall_health']}")
            print(f"RECOMMENDED ACTION: {result['priority_action']}")
            
            # Detailed analysis
            if result.get('bearing_analysis'):
                print(f"\nBEARING ANALYSIS:")
                print(f"  Status: {result['bearing_analysis']['fault_type']}")
                print(f"  Confidence: {result['bearing_analysis']['confidence']:.1%}")
            
            if result.get('motor_analysis'):
                print(f"\nMOTOR ANALYSIS:")
                print(f"  Status: {result['motor_analysis']['status']}")
                print(f"  Confidence: {result['motor_analysis']['confidence']:.1%}")
            
            if result.get('electrical_analysis'):
                print(f"\nELECTRICAL ANALYSIS:")
                print(f"  Status: {result['electrical_analysis']['status']}")
                print(f"  Confidence: {result['electrical_analysis']['confidence']:.1%}")
            
            print("="*70)
            
        else:
            print(f"✗ Diagnosis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Diagnosis error: {e}")
    
    # Step 3: Check Prediction Logs
    print("\n[STEP 3] Prediction Logs")
    print("-" * 70)
    
    try:
        logs_response = requests.get(
            f"{API_URL}/api/v1/auth/logs",
            headers=headers
        )
        
        if logs_response.status_code == 200:
            logs = logs_response.json()
            print(f"✓ Retrieved {len(logs)} prediction logs")
            
            if logs:
                latest = logs[0]
                print(f"\nLatest Prediction:")
                print(f"  Model: {latest['model_used']}")
                print(f"  RUL: {latest['rul_prediction']} hours")
                print(f"  Faults: {latest['fault_detected']}")
                print(f"  Response Time: {latest['response_time_ms']} ms")
        else:
            print(f"✗ Failed to retrieve logs: {logs_response.text}")
            
    except Exception as e:
        print(f"✗ Logs error: {e}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_complete_system()
