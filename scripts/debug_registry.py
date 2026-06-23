import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

print("Attempting to load model registry...")
try:
    from backend.app.services.model_registry import registry
    print("Import successful. Loading models...")
    registry.load_models()
    print("Models loaded successfully.")
    print(f"Loaded models: {list(registry.models.keys())}")
except Exception as e:
    print(f"FAILED to load models: {e}")
    import traceback
    traceback.print_exc()
