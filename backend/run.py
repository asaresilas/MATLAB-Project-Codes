"""
MotorGuard — API server entry point.

Environment variables (all optional — defaults suit local development):
  HOST             Bind address. Default: 127.0.0.1 (loopback only).
                   Set to 0.0.0.0 ONLY behind a reverse proxy with TLS.
  PORT             Port number. Default: 8000.
  LOG_LEVEL        Uvicorn log level (debug/info/warning/error). Default: info.
  JWT_SECRET_KEY   Required for persistent JWT sessions across restarts.
  CORS_ORIGINS     Comma-separated list of allowed origins. Default: localhost only.
"""

import os
import warnings
import sys

# ── Silence TensorFlow verbose startup noise (before any TF import) ───────────
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")         # suppress TF C++ INFO/WARNING logs
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")        # suppress oneDNN floating-point warnings
os.environ.setdefault("TF_KERAS_BACKEND", "tensorflow")

# ── Suppress sklearn/xgboost version-mismatch PickleWarnings ─────────────────
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")

# ── Check port availability before wasting 30 s on model loading ─────────────
def _port_is_free(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

# ── Pre-flight checks ─────────────────────────────────────────────────────────
if not os.getenv("JWT_SECRET_KEY"):
    warnings.warn(
        "\n"
        "  JWT_SECRET_KEY is not set — a random key will be used and all\n"
        "  sessions will be invalidated on every restart.\n"
        "  Set this variable before any production deployment.",
        RuntimeWarning,
        stacklevel=1,
    )

_host      = os.getenv("HOST",      "127.0.0.1")
_port      = int(os.getenv("PORT",  "8000"))
_log_level = os.getenv("LOG_LEVEL", "info").lower()

if _host == "0.0.0.0":
    warnings.warn(
        "HOST=0.0.0.0 — binding to all interfaces. "
        "Ensure a TLS-terminating reverse proxy is in front of this process.",
        RuntimeWarning,
        stacklevel=1,
    )

if __name__ == "__main__":
    # ── Early port check — fast-fail before TF even loads ─────────────────────
    if not _port_is_free(_host, _port):
        print(
            f"\n"
            f"  *** ERROR: Port {_port} is already in use! ***\n"
            f"\n"
            f"  Another copy of the backend is still running.\n"
            f"  Fix: open Task Manager, find python.exe, click End Task.\n"
            f"  Or run:  netstat -ano | findstr :{_port}\n"
            f"  Then:    taskkill /F /PID <the PID shown>\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"\n"
        f"  MotorGuard API -- starting up\n"
        f"  Loading TensorFlow + AI models (please wait ~30 s)...\n"
        f"  Server will be ready at  http://{_host}:{_port}\n"
    )

    import logging

    # ── Suppress noisy /health polling from the access log ────────────────────
    # The login page polls /health every few seconds; logging every 200 OK
    # floods the terminal and obscures real events.
    class _HealthFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            msg = record.getMessage()
            return 'GET /health' not in msg and 'GET /api/v1/health' not in msg

    for _logger_name in ('uvicorn.access', 'uvicorn'):
        _lg = logging.getLogger(_logger_name)
        _lg.addFilter(_HealthFilter())

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=_host,
        port=_port,
        reload=False,
        log_level=_log_level,
        workers=1,   # >1 workers require a process-safe session store
    )
