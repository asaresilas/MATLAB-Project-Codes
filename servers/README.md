# 🚀 Server Startup Scripts

This folder contains all API server startup and configuration scripts.

## Scripts

### Main Server Launcher
- **run_server.py** - Primary server startup script
- **start_server.bat** - Windows batch launcher
- **RUN_SERVER.bat** - Alternative batch launcher

### API Server
- **start_api_server.py** - FastAPI server initialization
- **simple_start.py** - Quick server startup
- **quick_server_check.py** - Health check utility

### Debugging & Diagnostics
- **run_server_debug.py** - Debug mode with detailed logging
- **diagnose_server.py** - Server diagnostics and troubleshooting

## Quick Start

```bash
# Option 1: Python (Recommended)
python run_server.py

# Option 2: Batch file (Windows)
.\start_server.bat

# Option 3: Simple start
python simple_start.py
```

## Expected Output

```
================================================================================
Project Root: <path to project>
Backend Dir: <path to backend>
================================================================================
[1] Testing Python environment...
    ✓ uvicorn installed
    ✓ TensorFlow installed
    ✓ FastAPI installed
[2] Starting server on http://0.0.0.0:8002
    Models loading... (this may take 30-60 seconds)
    Watch for: 'Application startup complete'
Press CTRL+C to stop
================================================================================
```

## Typical Startup Times

- **Python Environment Check**: ~2-3 seconds
- **Model Loading**: ~30-60 seconds (TensorFlow loading all 6 models)
- **Server Ready**: ~35-65 seconds total

## Server Address

- **Local**: http://localhost:8002
- **Remote**: http://0.0.0.0:8002
- **Health Check**: http://localhost:8002/health
- **API Docs**: http://localhost:8002/docs

## Troubleshooting

### Server won't start
```bash
python diagnose_server.py  # Run diagnostics
```

### Models taking too long to load
- This is normal for first startup (TensorFlow initialization)
- Models are cached after first load for faster subsequent starts

### Port already in use
- Change port in run_server.py or start_server.bat
- Default: 8002

## Integration with Tests

Tests automatically start/stop the server when needed:
```bash
python ../run_api_test.py  # Automatically manages server lifecycle
```

## Debug Mode

For detailed logging:
```bash
python run_server_debug.py
```

---

See also: [Server Testing](../server_testing/README.md)
