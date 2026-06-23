import sys
import os
import numpy as np
import json

# Add backend to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'backend')
sys.path.append(backend_path)

# Enable verbose output
import logging
logging.basicConfig(level=logging.INFO)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_nasa_prediction():
    print("Testing NASA API Endpoint...")
    
    # Check what models are loaded
    print("\nChecking loaded models...")
    models_response = client.get("/api/v1/models")
    print(f"Models endpoint status: {models_response.status_code}")
    if models_response.status_code == 200:
        print("Loaded models:", json.dumps(models_response.json(), indent=2))
    
    # 1. Generate dummy vibration data (1 second at 12kHz)
    fs = 12000
    t = np.linspace(0, 1, fs)
    vibration = 0.5 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(fs)
    
    # 2. Prepare payload
    payload = {
        "signal": vibration.tolist()
    }
    
    # 3. Send Request
    print("\nSending POST request to /api/v1/predict/nasa...")
    try:
        response = client.post("/api/v1/predict/nasa", json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
            if "rul" in data and isinstance(data["rul"], (int, float)):
                print("\n✓ SUCCESS: API returned valid RUL.")
            else:
                print("\n✗ FAILURE: Invalid response format.")
        else:
            print("\n✗ FAILURE: API Error")
            print(response.text)
            
    except Exception as e:
        print(f"\n✗ FAILURE: Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nasa_prediction()
