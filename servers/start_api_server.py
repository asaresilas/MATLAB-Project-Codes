import sys
import os
import subprocess
from pathlib import Path

# Get the project root and backend directory
project_root = Path(__file__).parent.resolve()
backend_dir = project_root / "backend"

print("=" * 80)
print("PREDICTIVE MAINTENANCE API SERVER")
print("=" * 80)
print(f"Project Root: {project_root}")
print(f"Backend Dir: {backend_dir}")
print("=" * 80)

# Check if backend directory exists
if not backend_dir.exists():
    print(f"\nERROR: Backend directory not found at {backend_dir}")
    sys.exit(1)

print("\n[1] Testing Python environment...")
try:
    import uvicorn
    print("  ✓ uvicorn installed")
except ImportError as e:
    print(f"  ✗ uvicorn not found: {e}")
    print("    Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    import tensorflow
    print("  ✓ TensorFlow installed")
except ImportError:
    print("  ✗ TensorFlow not found")

try:
    import fastapi
    print("  ✓ FastAPI installed")
except ImportError:
    print("  ✗ FastAPI not found")

print("\n[2] Starting server on http://0.0.0.0:8000")
print("    Models loading... (this may take 30-60 seconds)")
print("    Watch for: 'Application startup complete'")
print("\nPress CTRL+C to stop")
print("=" * 80)
print()

# Run uvicorn from backend directory to ensure proper imports
try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ], cwd=str(backend_dir))
except KeyboardInterrupt:
    print("\n" + "=" * 80)
    print("SERVER STOPPED")
    print("=" * 80)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

