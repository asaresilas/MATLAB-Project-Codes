"""
Test script for API Key Authentication

This script demonstrates:
1. How to generate an API key with username/password
2. How to use the API key for predictions
3. How to test all endpoints
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

print("="*80)
print("API KEY AUTHENTICATION TEST")
print("="*80)

# Step 1: Generate API Key
print("\n[STEP 1] Generate API Key")
print("-"*80)
print("logging in with username: admin, password from ADMIN_PASSWORD env var")

response = requests.post(
    f"{API_BASE}/api-keys/generate",
    json={"username": "admin", "password": os.getenv("ADMIN_PASSWORD", "")}
)

if response.status_code == 200:
    data = response.json()
    api_key = data["api_key"]
    print(f"✓ API Key Generated!")
    print(f"  Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"  User: {data['username']}")
    print(f"  Created: {data['created_at']}")
    print(f"\n  {data['message']}")
else:
    print(f"✗ Failed: {response.status_code}")
    print(response.text)
    exit(1)

# Step 2: Test API Key
print("\n[STEP 2] Test API Key")
print("-"*80)

headers = {"X-API-Key": api_key}
response = requests.get(f"{API_BASE}/api-keys/test", headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"✓ API Key is valid!")
    print(f"  User: {data['user']['full_name']}")
    print(f"  Email: {data['user']['email']}")
else:
    print(f"✗ Failed: {response.status_code}")
    print(response.text)

# Step 3: List Models (using API key)
print("\n[STEP 3] List Available Models")
print("-"*80)

response = requests.get(f"{API_BASE}/models", headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Found {len(data['loaded_models'])} models:")
    for model in data['loaded_models']:
        print(f"  - {model}")
else:
    print(f"✗ Failed: {response.status_code}")

# Step 4: Make a prediction (using API key)
print("\n[STEP 4] Test Prediction with API Key")
print("-"*80)
print("Testing CIA-1 endpoint...")

import numpy as np
test_signal = np.random.randn(12000).tolist()

response = requests.post(
    f"{API_BASE}/predict/cia1",
    headers=headers,
    json={"signal": test_signal}
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Prediction successful!")
    print(f"  Predicted Class: {data['predicted_class']}")
    print(f"  Confidence: {data['confidence']:.4f}")
else:
    print(f"✗ Failed: {response.status_code}")
    print(response.text)

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\n✓ API Key authentication is working!")
print(f"\nYour API Key: {api_key}")
print("\nTo use this key in your applications:")
print("  1. Include it in the 'X-API-Key' header")
print("  2. Example:")
print(f'     headers = {{"X-API-Key": "{api_key[:20]}..."}}"')
print("     response = requests.post(url, headers=headers, json=data)")
print("\n" + "="*80)
