"""
Minimal test to see if the app can import
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

print("Testing imports...")
try:
    from app.main import app
    print("SUCCESS! App imported without errors.")
    print("\nNow starting server...")
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
