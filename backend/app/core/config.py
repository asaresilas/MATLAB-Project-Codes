import os
import json
from pathlib import Path

class Settings:
    # backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> Project Root
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    CONFIG_PATH = os.path.join(BASE_DIR, "backend", "deployment_config.json")
    MODEL_DIR = os.path.join(BASE_DIR, "models")

    def load_deployment_config(self):
        if not os.path.exists(self.CONFIG_PATH):
            raise FileNotFoundError(f"Deployment config not found at {self.CONFIG_PATH}")
        
        with open(self.CONFIG_PATH, "r") as f:
            return json.load(f)

settings = Settings()
