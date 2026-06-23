import requests
import base64
import os
import random
import glob

API_URL = "http://localhost:8000/api/v1/predict/thermal"
DATA_DIR = r"datasets/Thermal"

# Find all images in Thermal dataset
image_paths = glob.glob(os.path.join(DATA_DIR, "*", "*.bmp"))

if not image_paths:
    print(f"Error: No images found in {DATA_DIR}")
    exit(1)

# Pick a random image
test_image_path = random.choice(image_paths)
true_label = os.path.basename(os.path.dirname(test_image_path))

print(f"Testing with image: {test_image_path}")
print(f"True Label: {true_label}")

# Encode image to Base64
with open(test_image_path, "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

# Create payload
payload = {
    "image": base64_image
}

print("\nSending request to API...")
try:
    response = requests.post(API_URL, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\nPrediction Result:")
        print(f"  Predicted Class: {result['predicted_class']}")
        print(f"  Confidence: {result['confidence']:.4f}")
        
        if result['predicted_class'] == true_label:
            print("\nRESULT: PASS (Match!)")
        else:
            print("\nRESULT: FAIL (Mismatch, but API functional)")
            
        print("\nTop 3 Probabilities:")
        # Sort probabilities and show top 3
        probs = sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True)
        for cls, prob in probs[:3]:
            print(f"  {cls}: {prob:.4f}")
    else:
        print(f"Error Response: {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
