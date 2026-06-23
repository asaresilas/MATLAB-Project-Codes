import base64
import io
import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from app.services.model_registry import registry
from datetime import datetime

class ThermalService:
    @staticmethod
    def process_and_predict(image_base64: str):
        """
        Processes a base64 encoded thermal image and returns predictions.
        """
        model = registry.get_model("Thermal")
        if not model:
            return {"error": "Thermal model not loaded"}
        
        try:
            # 1. Decode Base64 Image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # 2. Resize to (224, 224)
            image = image.resize((224, 224))
            
            # 3. Preprocess
            img_array = np.array(image)
            img_array = np.expand_dims(img_array, axis=0) # (1, 224, 224, 3)
            img_array = preprocess_input(img_array.astype(np.float32))
            
            # 4. Predict
            prediction = model.predict(img_array, verbose=0)
            
            # Class Names (Alphabetical Order from Training Directory)
            class_names = [
                'A10', 'A30', 'A50', 'A_B50', 
                'A_C10', 'A_C30', 'A_C_B10', 'A_C_B30', 
                'Fan', 'Noload', 'Rotor-0'
            ]
            
            predicted_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][predicted_idx])
            predicted_class = class_names[predicted_idx]
            
            probs = {name: float(prob) for name, prob in zip(class_names, prediction[0])}
            
            # Determine alert_level for consistency with other models
            # In thermal, any non-Normal class is a Warning or Critical
            if predicted_class in ['Noload', 'Fan', 'Rotor-0']:
                 alert_level = "NORMAL"
            elif confidence > 0.8:
                 alert_level = "CRITICAL"
            else:
                 alert_level = "WARNING"
            
            return {
                "type": "prediction_thermal",
                "predicted_class": predicted_class,
                "confidence": round(confidence, 4),
                "alert_level": alert_level,
                "probabilities": probs,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Thermal prediction failed: {str(e)}"}

thermal_service = ThermalService()
