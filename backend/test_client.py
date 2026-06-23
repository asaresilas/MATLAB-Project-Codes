import requests
import json
import random

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

def predict_failure(sensor_name, data):
    """
    Predicts failure based on the sensor name (dataset) and input data.
    
    Args:
        sensor_name (str): Name of the dataset/sensor (CIA1, NASA, CWRU, Induction, Current).
        data (dict): Input data for the model.
        
    Returns:
        dict: The prediction result.
    """
    # Map friendly names to API endpoints
    endpoints = {
        "CIA1": "/predict/cia1",
        "NASA": "/predict/nasa",
        "CWRU": "/predict/cwru",
        "Induction": "/predict/induction",
        "Current": "/predict/current"
    }
    
    if sensor_name not in endpoints:
        print(f"Error: Unknown sensor name '{sensor_name}'. Available: {list(endpoints.keys())}")
        return None
        
    url = f"{BASE_URL}{endpoints[sensor_name]}"
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() # Raise error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server Response: {e.response.text}")
        return None

# --- Example Usage ---

if __name__ == "__main__":
    print("--- Testing Predictive Maintenance API ---\n")

    # 1. Test CIA-1 (Process Data)
    print("1. Testing CIA-1 (Process Sensors)...")
    cia1_data = {
        "type": "L",
        "air_temperature": 298.1,
        "process_temperature": 308.6,
        "rotational_speed": 1551,
        "torque": 42.8,
        "tool_wear": 0
    }
    print(f"   Input: {cia1_data}")
    result = predict_failure("CIA1", cia1_data)
    if result:
        print(f"   Prediction: {result['predicted_class']} (Confidence: {result['confidence']:.2f})")
    print("-" * 30)

    # 2. Test NASA (Turbofan Engine)
    print("\n2. Testing NASA (Turbofan Engine RUL)...")
    # Generate dummy sequence (30 time steps, 36 features)
    # In reality, this would be real sensor data
    nasa_data = {
        "data": [[random.random() for _ in range(36)] for _ in range(30)]
    }
    print(f"   Input: [Sequence of 30 time steps x 36 features]")
    result = predict_failure("NASA", nasa_data)
    if result:
        print(f"   Predicted RUL: {result['rul']:.2f} cycles")
    print("-" * 30)

    # 3. Test CWRU (Bearing Vibration)
    print("\n3. Testing CWRU (Bearing Vibration)...")
    # Generate dummy signal (1000 data points)
    cwru_data = {
        "signal": [random.random() for _ in range(1000)]
    }
    print(f"   Input: [Signal of length 1000]")
    result = predict_failure("CWRU", cwru_data)
    if result:
        print(f"   Prediction: {result['predicted_class']} (Confidence: {result['confidence']:.2f})")
    print("-" * 30)
