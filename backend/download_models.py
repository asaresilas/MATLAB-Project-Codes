"""
download_models.py — Download trained models from Hugging Face Hub.

Called automatically at Docker build time and again at container startup
if Trained_models/ is empty. Set HF_MODEL_REPO to your HF Hub model repo
(e.g. "your-username/motorguard-models").

Usage:
    python download_models.py
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[download_models] %(message)s")
log = logging.getLogger(__name__)

TRAINED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "Trained_models")
MODELS_SUBDIR = os.path.join(os.path.dirname(__file__), "..", "models")


def models_already_present() -> bool:
    """Return True if Trained_models/ is non-empty (skip re-download)."""
    if not os.path.isdir(TRAINED_MODELS_DIR):
        return False
    for root, dirs, files in os.walk(TRAINED_MODELS_DIR):
        if any(f.endswith((".keras", ".pkl", ".h5")) for f in files):
            return True
    return False


def download():
    repo_id = os.environ.get("HF_MODEL_REPO", "")

    if not repo_id:
        log.warning(
            "HF_MODEL_REPO environment variable is not set. "
            "Set it to your Hugging Face model repo (e.g. 'your-username/motorguard-models'). "
            "Skipping model download — backend will start without models."
        )
        return

    if models_already_present():
        log.info("Models already present in Trained_models/ — skipping download.")
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        log.error(
            "huggingface_hub is not installed. "
            "Add 'huggingface_hub' to requirements.txt and rebuild."
        )
        sys.exit(1)

    log.info(f"Downloading models from HF Hub repo: {repo_id}")
    log.info("This may take a few minutes on first start...")

    os.makedirs(TRAINED_MODELS_DIR, exist_ok=True)

    try:
        snapshot_download(
            repo_id=repo_id,
            repo_type="model",
            local_dir=TRAINED_MODELS_DIR,
            ignore_patterns=["*.git*", "*.gitattributes"],
        )
        log.info(f"Models downloaded successfully to: {os.path.abspath(TRAINED_MODELS_DIR)}")
    except Exception as e:
        log.error(f"Failed to download models: {e}")
        log.error("Backend will start but all model inference will return 503.")


if __name__ == "__main__":
    download()
