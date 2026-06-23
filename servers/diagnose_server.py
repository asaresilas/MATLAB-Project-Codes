"""
Test if the server can start at all - diagnose startup issues
"""
import sys
import os

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

print("Step 1: Testing imports...")
try:
    import uvicorn
    print("  ✓ uvicorn imported")
except Exception as e:
    print(f"  ✗ uvicorn import failed: {e}")
    exit(1)

try:
    from backend.app.main import app
    print("  ✓ app imported")
except Exception as e:
    print(f"  ✗ app import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nStep 2: Testing model registry...")
try:
    from backend.app.services.model_registry import registry
    print("  ✓ registry imported")
    
    print("\nStep 3: Loading models...")
    registry.load_models()
    
    print(f"\n✓ SUCCESS! Loaded {len(registry.models)} models:")
    for name in registry.models.keys():
        print(f"  - {name}")
    
    print("\nThe server should work. Try starting it with:")
    print("  .venv\\Scripts\\python.exe backend/run.py")
    
except Exception as e:
    print(f"  ✗ Model loading failed: {e}")
    import traceback
    traceback.print_exc()
