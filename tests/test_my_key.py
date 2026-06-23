"""
Quick API Test with Your API Key

Replace YOUR_API_KEY_HERE with the key you just received
"""

import requests
import numpy as np

# ============================================
# STEP 1: PUT YOUR API KEY HERE
# ============================================
API_KEY = "sk_admin_UxRL1YX0b45vhivqM-p7aHuygr_6Qtk8KJj6yQ9jUSI"  # <-- Replace this!

# ============================================
# STEP 2: Run this script
# ============================================

API_BASE = "http://localhost:8000/api/v1"
headers = {"X-API-Key": API_KEY}

print("="*80)
print("TESTING API WITH YOUR KEY")
print("="*80)

# Test 1: List models
print("\n[1] Listing available models...")
response = requests.get(f"{API_BASE}/models", headers=headers)
if response.status_code == 200:
    models = response.json()["loaded_models"]
    print(f"✓ Found {len(models)} models:")
    for model in models:
        print(f"  - {model}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)
    exit(1)

# Test 2: Make a prediction
print("\n[2] Testing CIA-1 prediction...")
test_signal = np.random.randn(12000).tolist()

response = requests.post(
    f"{API_BASE}/predict/cia1",
    headers=headers,
    json={"signal": test_signal}
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Prediction successful!")
    print(f"  Class: {result['predicted_class']}")
    print(f"  Confidence: {result['confidence']:.4f}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)

print("\n" + "="*80)
print("SUCCESS! Your API key is working correctly.")
print("="*80)
