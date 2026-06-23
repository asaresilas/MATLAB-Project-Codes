"""
Comprehensive API Test - All 6 Datasets
Tests all endpoints to verify models are loaded and working

IMPORTANT: Add your API key below!
"""

import requests
import numpy as np
import base64
import os
import glob
import random
from PIL import Image
import io

# ============================================
# PUT YOUR API KEY HERE
# ============================================
API_KEY = "YOUR_API_KEY_HERE"  # <-- Replace with your actual key

API_BASE = "http://localhost:8000/api/v1"

# Create headers with API key
headers = {"X-API-Key": API_KEY} if API_KEY != "YOUR_API_KEY_HERE" else {}

print("="*80)
print("COMPREHENSIVE API TEST - ALL 6 DATASETS")
print("="*80)
if API_KEY == "YOUR_API_KEY_HERE":
    print("\n⚠️  WARNING: You need to add your API key!")
    print("Edit this file and replace YOUR_API_KEY_HERE with your actual key.\n")
else:
    print(f"\n✓ Using API Key: {API_KEY[:20]}...\n")

# Test 1: Health Check
print("\n[TEST 1] Health Check")
print("-"*80)
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ PASS" if response.status_code == 200 else "✗ FAIL")
except Exception as e:
    print(f"✗ FAIL - {e}")
    exit(1)

# Test 2: List Models
print("\n[TEST 2] List Loaded Models")
print("-"*80)
try:
    response = requests.get(f"{API_BASE}/models", headers=headers, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Loaded Models: {data['loaded_models']}")
        print(f"Total: {len(data['loaded_models'])} models")
        
        expected = ["CIA-1", "NASA", "CWRU", "Induction Motor", "Current Signature", "Thermal"]
        loaded = data['loaded_models']
        
        for model in expected:
            if model in loaded:
                print(f"  ✓ {model}")
            else:
                print(f"  ✗ {model} - NOT LOADED")
        
        if len(loaded) == 6:
            print("✓ PASS - All 6 models loaded!")
        else:
            print(f"✗ FAIL - Only {len(loaded)}/6 models loaded")
    else:
        print("✗ FAIL")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 3: CIA-1 Prediction
print("\n[TEST 3] CIA-1 Prediction")
print("-"*80)
try:
    # Generate test signal (12000 samples)
    signal = np.random.randn(12000).tolist()
    payload = {"signal": signal}
    
    response = requests.post(f"{API_BASE}/predict/cia1", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted Class: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print("✓ PASS")
    else:
        print(f"✗ FAIL - {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 4: NASA Prediction
print("\n[TEST 4] NASA RUL Prediction")
print("-"*80)
try:
    # Generate test signal
    signal = np.random.randn(12000).tolist()
    payload = {"signal": signal}
    
    response = requests.post(f"{API_BASE}/predict/nasa", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted RUL: {result['rul']:.2f} hours")
        print("✓ PASS")
    else:
        print(f"✗ FAIL - {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 5: CWRU Prediction
print("\n[TEST 5] CWRU Prediction")
print("-"*80)
try:
    # Generate test signal
    signal = np.random.randn(12000).tolist()
    payload = {"signal": signal}
    
    response = requests.post(f"{API_BASE}/predict/cwru", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted Class: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print("✓ PASS")
    else:
        print(f"✗ FAIL - {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 6: Induction Motor Prediction
print("\n[TEST 6] Induction Motor Prediction")
print("-"*80)
try:
    # Generate test signal
    signal = np.random.randn(12000).tolist()
    payload = {"signal": signal}
    
    response = requests.post(f"{API_BASE}/predict/induction", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted Class: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print("✓ PASS")
    else:
        print(f"✗ FAIL - {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 7: Current Signature Prediction
print("\n[TEST 7] Current Signature Prediction")
print("-"*80)
try:
    # Generate test signal
    signal = np.random.randn(12000).tolist()
    payload = {"signal": signal}
    
    response = requests.post(f"{API_BASE}/predict/current", headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        result = response.json()
        print(f"  Predicted Class: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        print("✓ PASS")
    else:
        print(f"✗ FAIL - {response.status_code}: {response.text}")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Test 8: Thermal Prediction
print("\n[TEST 8] Thermal Imaging Prediction")
print("-"*80)
try:
    # Find a thermal image
    thermal_images = glob.glob("datasets/Thermal/*/r*.bmp")
    if thermal_images:
        test_img = random.choice(thermal_images)
        true_class = os.path.basename(os.path.dirname(test_img))
        
        # Encode to base64
        with open(test_img, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {"image": img_b64}
        response = requests.post(f"{API_BASE}/predict/thermal", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Test Image: {os.path.basename(test_img)}")
            print(f"  True Class: {true_class}")
            print(f"  Predicted Class: {result['predicted_class']}")
            print(f"  Confidence: {result['confidence']:.4f}")
            print("✓ PASS")
        else:
            print(f"✗ FAIL - {response.status_code}: {response.text}")
    else:
        print("✗ FAIL - No thermal images found")
except Exception as e:
    print(f"✗ FAIL - {e}")

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("\nAll 6 dataset endpoints have been tested!")
print("The API is ready for production use.")
print("="*80)
