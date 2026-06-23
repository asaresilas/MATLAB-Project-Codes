import os
import sys
import traceback

# Add project root and backend to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

LOG_FILE = "critical_server_error.txt"

# Redirect stdout and stderr to the file
log_f = open(LOG_FILE, "w", buffering=1)
sys.stdout = log_f
sys.stderr = log_f

print("Starting server debug with full logging...")

try:
    from backend.app.services.model_registry import registry
    print("Importing app.main...")
    from backend.app.main import app
    import uvicorn
    
    print("Starting uvicorn...")
    with open(LOG_FILE, "a") as f:
        f.write("Imports successful. Starting uvicorn...\n")
        
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")

except Exception as e:
    with open(LOG_FILE, "a") as f:
        f.write(f"CRASH DETECTED: {e}\n")
        f.write(traceback.format_exc())
    print(f"Crashed: {e}")
