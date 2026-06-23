import sys
import os
import uvicorn

# Force absolute path discovery
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

if __name__ == "__main__":
    print(f"--- PROJECT ROOT: {project_root} ---")
    print("--- STARTING PREDICTIVE MAINTENANCE AI (PORT 8001) ---")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8001, reload=False)
