"""
Simple API Server Starter - Keeps running until you press Ctrl+C
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

print("="*80)
print("STARTING API SERVER")
print("="*80)
print("\nImporting modules...")

try:
    from app.main import app
    import uvicorn
    print("✓ Modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

print("\n" + "="*80)
print("SERVER STARTING ON http://localhost:8000")
print("="*80)
print("\nWait for 'Application startup complete' message...")
print("Then open a NEW terminal and run:")
print("  .venv\\Scripts\\python.exe tests\\test_api_key_auth.py")
print("\nPress Ctrl+C to stop the server")
print("="*80 + "\n")

try:
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
except Exception as e:
    print(f"\n✗ Server error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
