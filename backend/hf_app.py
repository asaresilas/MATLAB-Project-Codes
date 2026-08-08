"""
hf_app.py — Hugging Face Spaces entry point (Gradio SDK).

Copy this file to your HF Space root as app.py.

HF Spaces runs this file and serves the returned ASGI `app` on port 7860.
We mount our FastAPI backend into Gradio so ALL FastAPI endpoints
(/api/v1/..., /ws/..., /health, /docs) are accessible at the Space URL.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[HF-Space] %(message)s")

# ── Silence TensorFlow noise ──────────────────────────────────────────────────
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_KERAS_BACKEND", "tensorflow")

# HF Spaces exposes port 7860
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "7860")

# ── Download models from HF Hub (skipped if already present) ─────────────────
sys.path.insert(0, os.path.dirname(__file__))
import download_models
download_models.download()

# ── Import our FastAPI application ────────────────────────────────────────────
from app.main import app as fastapi_app   # noqa: E402  (after env setup)

# ── Minimal Gradio status page ────────────────────────────────────────────────
import gradio as gr

with gr.Blocks(title="MotorGuard API") as _demo:
    gr.Markdown("""
    # ⚙️ MotorGuard — Predictive Maintenance API

    The FastAPI backend is running. Use the links below:

    | Resource | URL |
    |---|---|
    | Interactive API docs | [/docs](/docs) |
    | Health check | [/health](/health) |
    | Predict (HTTP POST) | `/api/v1/predict/simulink` |
    | Dashboard WebSocket | `wss://asaresilas-motorguard.hf.space/ws/dashboard` |

    **MATLAB connection:**
    ```matlab
    setenv('MOTORGUARD_SERVER', 'https://asaresilas-motorguard.hf.space')
    ```
    """)

# ── Mount Gradio UI into the FastAPI app ─────────────────────────────────────
# gr.mount_gradio_app returns a new ASGI app (FastAPI + Gradio at /ui).
# HF Spaces detects the `app` variable and serves it on port 7860.
# All FastAPI routes (/api/v1/..., /ws/..., /docs) remain accessible.
app = gr.mount_gradio_app(fastapi_app, _demo, path="/ui")
