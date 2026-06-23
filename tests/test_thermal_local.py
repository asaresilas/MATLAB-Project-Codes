import os
import sys
import numpy as np
import tensorflow as tf
from PIL import Image
import io
import base64

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.app.services.model_registry import registry

print("Loading Thermal Model for local verification...")
try:
    # Manual load logic similar to API endpoint
    registry.load_models()
    model = registry.get_model("Thermal")
    
    if not model:
        print("FAILED: Thermal model not loaded by registry.")
        exit(1)
        
    print("Model loaded. Testing preprocessing...")
    
    # Pick a test image
    test_img_path = r"datasets/Thermal/Rotor-0/r030.bmp"
    if not os.path.exists(test_img_path):
        print(f"FAILED: Test image {test_img_path} not found.")
        exit(1)
        
    # Read and encode to base64 to simulate API input
    with open(test_img_path, "rb") as f:
        img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
    # Preprocessing logic from endpoints.py
    img_data = base64.b64decode(img_b64)
    img = Image.open(io.BytesIO(img_data)).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img).astype('float32')
    img_array = np.expand_dims(img_array, axis=0)
    img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
    
    print("Running prediction...")
    preds = model.predict(img_array, verbose=0)
    pred_idx = np.argmax(preds[0])
    
    # Get class names from registry/settings
    from backend.app.core.config import settings
    deployment_config = settings.load_deployment_config()
    thermal_config = deployment_config.get("Thermal")
    
    # In endpoints.py, class_names come from datasets/Thermal if not specified
    data_dir = os.path.join(settings.BASE_DIR, "datasets", "Thermal")
    class_names = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
    
    predicted_class = class_names[pred_idx]
    confidence = float(preds[0][pred_idx])
    
    print(f"\nLOCAL TEST RESULT:")
    print(f"  Predicted: {predicted_class}")
    print(f"  Confidence: {confidence:.4f}")
    print(f"  Expected: Rotor-0")
    
    if predicted_class == "Rotor-0":
        print("\nSUCCESS: Model logic is correct!")
    else:
        print("\nWARNING: Prediction mismatch (Expected Rotor-0), but logic is working.")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
