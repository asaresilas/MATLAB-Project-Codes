"""
FastAPI application entry point.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Path bootstrap (allows running from project root or backend/) ──────────────
_current = os.path.abspath(__file__)
_backend_dir = os.path.dirname(os.path.dirname(_current))
_project_root = os.path.dirname(_backend_dir)
sys.path.insert(0, _project_root)
sys.path.insert(0, _backend_dir)

from app.api import endpoints, comprehensive, api_key_routes, websocket_handler
from app.auth import oauth
from app.services.model_registry import registry
from app.database import init_db

logger = logging.getLogger(__name__)

# ── Startup timestamp (for uptime reporting in /health/detailed) ──────────────
_started_at = datetime.now(timezone.utc)


# ── CORS origins ──────────────────────────────────────────────────────────────
# In development: set CORS_ORIGINS="" or omit → only localhost is allowed.
# In production:  set CORS_ORIGINS="https://dashboard.example.com,https://ops.example.com"
_cors_env = os.getenv("CORS_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env.strip()
    else [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
)


# ── JWT key guard ─────────────────────────────────────────────────────────────
_jwt_key = os.getenv("JWT_SECRET_KEY", "")
if not _jwt_key:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY is not set — tokens will be invalidated on every restart. "
        "Set this variable before any production deployment.",
        RuntimeWarning,
        stacklevel=1,
    )


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio as _asyncio
    logger.info("=== MotorGuard API starting up ===")
    logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)
    # Initialise database — creates sensor_readings and other tables if not present
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database init failed (non-fatal): %s", exc)

    # Load models in a thread-pool executor so the async event loop stays free.
    # This means /health responds immediately even while TF models are loading,
    # which prevents MATLAB's HTTP health-check from timing out.
    logger.info("Loading AI models in background thread (server accepts requests immediately)…")
    await _asyncio.to_thread(registry.load_models)

    n = len(registry.models)
    if n == 0:
        logger.warning("⚠ No models loaded — all inference endpoints will return 503")
    else:
        logger.info("✓ %d model(s) ready", n)

    # ── Model warmup — run one dummy inference per loaded model so TensorFlow
    # JIT-compiles all compute graphs NOW, not on MATLAB's first live call.
    # Without this, the very first MATLAB prediction takes 10–30 s (timeout).
    if n > 0:
        import numpy as _np
        from app.api.websocket_handler import prediction_engine
        logger.info("Warming up models (dummy inference to pre-compile TF graphs)…")
        try:
            warmup_payload = {
                "vibration": _np.random.randn(2048).tolist(),
                "current":   _np.random.randn(1000, 3).tolist(),
                "scalars":   [1480.0, 97.3, 300.0, 293.0],  # Kelvin — same as MATLAB
            }
            await prediction_engine.predict(warmup_payload)
            logger.info("✓ Model warmup complete — all TF graphs compiled, ready for MATLAB")
        except Exception as _e:
            logger.warning("Warmup inference failed (non-fatal): %s", _e)

    yield
    logger.info("=== MotorGuard API shutting down ===")


# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MotorGuard — Predictive Maintenance Digital Twin API",
    description=(
        "Real-time motor health monitoring via multi-modal AI inference. "
        "Authenticate with POST /api/v1/auth/token (Bearer) or "
        "POST /api/v1/api-keys/generate (X-API-Key)."
    ),
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Accept", "Origin"],
    expose_headers=["Content-Type"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(endpoints.router,               prefix="/api/v1")
app.include_router(comprehensive.router,           prefix="/api/v1")
app.include_router(api_key_routes.router,          prefix="/api/v1")
app.include_router(oauth.router,                   prefix="/api/v1")
app.include_router(websocket_handler.router)          # /ws/simulink/…  (no prefix)
app.include_router(websocket_handler.rest_router)     # /api/v1/predict/simulink


# ── Health endpoints ───────────────────────────────────────────────────────────

@app.get("/", tags=["meta"])
async def root():
    return {"message": "MotorGuard Predictive Maintenance API", "docs": "/docs"}


@app.get("/health", tags=["meta"],
         summary="Basic liveness probe — always 200 if the process is up")
async def health_liveness():
    """Kubernetes/load-balancer liveness probe. Returns 200 as long as the
    process is alive (models may not be loaded yet)."""
    return {"status": "alive", "uptime_s": _uptime_seconds()}


@app.get("/health/ready", tags=["meta"],
         summary="Readiness probe — 200 only when ≥1 model is loaded")
async def health_readiness():
    """Returns 200 when the API is ready to serve inference requests.
    Returns 503 if no models have loaded (e.g., right after startup)."""
    from fastapi import Response
    loaded = len(registry.models)
    if loaded == 0:
        return Response(
            content='{"status":"not_ready","reason":"no models loaded"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ready", "models_loaded": loaded}


@app.get("/health/detailed", tags=["meta"],
         summary="Full diagnostic — per-model load status, uptime, connections")
async def health_detailed():
    """Detailed health report for operators and monitoring dashboards."""
    from app.api.websocket_handler import manager
    return {
        "status": "ready" if registry.is_loaded() else "degraded",
        "uptime_s": _uptime_seconds(),
        "models": registry.health_detail(),
        "websocket": {
            "active_simulink_clients": manager.get_connection_count(),
            "active_dashboard_clients": len(manager.dashboard_connections),
        },
        "cors_origins": ALLOWED_ORIGINS,
    }


def _uptime_seconds() -> float:
    return (datetime.now(timezone.utc) - _started_at).total_seconds()
