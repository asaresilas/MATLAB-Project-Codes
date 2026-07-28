import base64
import io
import numpy as np
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from app.services.model_registry import registry
from datetime import datetime

# Shared constants
_CLASS_NAMES = [
    'A10', 'A30', 'A50', 'A_B50',
    'A_C10', 'A_C30', 'A_C_B10', 'A_C_B30',
    'Fan', 'Noload', 'Rotor-0'
]
_NORMAL_CLASSES = {'Noload', 'Fan', 'Rotor-0'}


def _alert_level(predicted_class: str, confidence: float) -> str:
    if predicted_class in _NORMAL_CLASSES:
        return "NORMAL"
    return "CRITICAL" if confidence > 0.8 else "WARNING"


def _run_model(img_rgb_uint8: np.ndarray) -> dict:
    """Shared inference step: (H, W, 3) uint8 → prediction dict."""
    model = registry.get_model("Thermal")
    if not model:
        return {"error": "Thermal model not loaded"}

    img = Image.fromarray(img_rgb_uint8, mode='RGB').resize((224, 224), Image.BICUBIC)
    batch = np.expand_dims(np.array(img, dtype=np.float32), axis=0)
    batch = preprocess_input(batch)
    prediction = model.predict(batch, verbose=0)

    predicted_idx   = int(np.argmax(prediction[0]))
    confidence      = float(prediction[0][predicted_idx])
    predicted_class = _CLASS_NAMES[predicted_idx]

    return {
        "type":            "prediction_thermal",
        "predicted_class": predicted_class,
        "confidence":      round(confidence, 4),
        "alert_level":     _alert_level(predicted_class, confidence),
        "probabilities":   {n: float(p) for n, p in zip(_CLASS_NAMES, prediction[0])},
        "timestamp":       datetime.now().isoformat(),
    }


class ThermalService:

    @staticmethod
    def predict_from_matrix(T_img):
        """
        Accept a 3×3 temperature matrix from Simulink (values in Kelvin).
        Builds the thermal image internally and returns a prediction.

        T_img: list of lists or 2-D array, shape (3, 3)
               [[Tst, Th,  Tst],
                [Tb,  Tc,  Tb ],
                [Tst, Th,  Tst]]  — float values in Kelvin
        """
        try:
            T = np.array(T_img, dtype=np.float32)
            if T.shape != (3, 3):
                # Accept flat 9-element list too
                T = T.reshape(3, 3)

            # Step 1 — Normalise to [0, 1]
            T_min, T_max = float(T.min()), float(T.max())
            if T_max == T_min:
                T_norm = np.zeros((3, 3), dtype=np.float32)
            else:
                T_norm = (T - T_min) / (T_max - T_min)

            # Step 2 — Apply jet colormap → RGB uint8 (3, 3, 3)
            import matplotlib
            matplotlib.use('Agg')          # non-interactive backend, safe for server
            import matplotlib.pyplot as plt
            cmap  = plt.get_cmap('jet')
            T_rgb = (cmap(T_norm)[:, :, :3] * 255).astype(np.uint8)  # drop alpha

            # Step 3 — Resize to 64×64 (matches MATLAB training pipeline)
            img64 = Image.fromarray(T_rgb, mode='RGB').resize((64, 64), Image.BICUBIC)
            img64_arr = np.array(img64, dtype=np.float32) / 255.0

            # Step 4 — Add Gaussian sensor noise (σ²=0.001, same as THERMAL_IMAGE_GENERATION.m)
            noise = np.random.normal(0, np.sqrt(0.001), img64_arr.shape).astype(np.float32)
            img64_arr = np.clip(img64_arr + noise, 0.0, 1.0)
            img64_uint8 = (img64_arr * 255).astype(np.uint8)

            return _run_model(img64_uint8)

        except Exception as e:
            return {"error": f"Thermal matrix prediction failed: {str(e)}"}

    @staticmethod
    def process_and_predict(image_base64: str):
        """
        Processes a base64 encoded thermal image and returns predictions.
        Accepts any valid JPEG/PNG/BMP encoded as a base64 string.
        """
        if not registry.get_model("Thermal"):
            return {"error": "Thermal model not loaded"}

        try:
            image_data = base64.b64decode(image_base64)
            image      = Image.open(io.BytesIO(image_data)).convert('RGB')
            img_uint8  = np.array(image, dtype=np.uint8)
            return _run_model(img_uint8)

        except Exception as e:
            return {"error": f"Thermal prediction failed: {str(e)}"}

thermal_service = ThermalService()
