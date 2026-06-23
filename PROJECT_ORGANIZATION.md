# Project Organization Guide

## Overview
This project has been reorganized for better clarity and maintainability. All server-related code is now grouped together, all testing code is grouped together, and utility scripts are separated.

## Folder Structure

```
Matlab_Project codes/
├── server_setup/                    # ✓ API SERVER SETUP
│   ├── backend/                     # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py              # Server entry point
│   │   │   ├── api/                 # Endpoints
│   │   │   │   ├── endpoints.py
│   │   │   │   ├── comprehensive.py
│   │   │   │   └── api_key_routes.py
│   │   │   ├── services/
│   │   │   │   └── model_registry.py # Model loading
│   │   │   ├── auth/                # Authentication
│   │   │   ├── schemas/             # Data models
│   │   │   ├── core/
│   │   │   │   └── config.py
│   │   │   └── database.py
│   │   ├── deployment_config.json   # Model paths config
│   │   ├── requirements.txt         # Backend dependencies
│   │   └── run.py
│   ├── START_API_SERVER.bat         # ⭐ Run this to start the API
│   ├── START_API_SERVER.ps1         # (PowerShell version)
│   └── deployment_config.json       # Model configuration
│
├── server_testing/                  # ✓ API TESTING & VALIDATION
│   ├── api_tests/
│   │   ├── test_all_models.py       # ⭐ Comprehensive test suite
│   │   ├── test_api_simple.py       # Simple tests
│   │   ├── test_api_key_auth.py     # Authentication tests
│   │   └── ... (other test files)
│   ├── logs/                        # Test result logs
│   └── README_TESTING.md            # Testing guide
│
├── utility_scripts/                 # HELPER SCRIPTS
│   ├── diagnose_server.py           # Diagnose server issues
│   ├── debug_registry.py            # Debug model loading
│   └── ... (other utility scripts)
│
├── Trained_models/                  # 📦 AI MODEL STORAGE
│   ├── cia1_dl/
│   ├── nasa_dl_comparison/
│   ├── cwru_cnn/
│   ├── induction_dl/
│   ├── current_signature_dl/
│   └── thermal/
│
├── models/                          # Additional models
│   ├── thermal/
│   └── ... (other model variants)
│
├── matlab_client/                   # 🎯 MATLAB INTEGRATION
│   ├── PredictiveMaintenanceAPI.m   # Main MATLAB client
│   ├── example_usage.m              # MATLAB example
│   └── ... (other MATLAB scripts)
│
├── notebooks/                       # 📓 JUPYTER NOTEBOOKS
│   ├── 01_DL_cnn_training.ipynb
│   ├── 02_NASA_DL_training.ipynb
│   └── ... (training notebooks)
│
├── src/                             # SOURCE CODE
│   ├── interface.py                 # Data processing
│   ├── features/
│   └── ... (other source files)
│
├── tests/                           # LEGACY TESTS (can be archived)
│
├── datasets/                        # DATA
│   ├── NASA/
│   ├── CWRU/
│   ├── CIA-1/
│   └── ... (other datasets)
│
├── docs/                            # DOCUMENTATION
│   ├── API_KEY_AUTH.md
│   ├── retraining_guide.md
│   └── technical_roadmap_v1.md
│
├── README.md                        # Project overview
├── requirements.txt                 # Main dependencies
└── .venv/                          # Python virtual environment

```

## Quick Start

### 1. Start the API Server

**Option A: Using Batch File (Windows Command Prompt)**
```bash
cd server_setup
START_API_SERVER.bat
```

**Option B: Using PowerShell**
```powershell
cd server_setup
.\START_API_SERVER.ps1
```

**Option C: Manual Start**
```bash
cd server_setup
..\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8002
```

Expected output:
```
Loading models from registry...
  Loading CIA1 model...
  Successfully loaded CIA1
  Loading NASA model...
  Successfully loaded NASA
  ...
  Application startup complete.
```

### 2. Test All Models and API

**Open a NEW terminal/PowerShell and run:**

```bash
cd server_testing\api_tests
python test_all_models.py
```

Or with custom URL:
```bash
python test_all_models.py http://localhost:8002
```

Expected output:
```
✓ Health Check: PASS
✓ Models Endpoint: PASS (6/6 models loaded)
✓ Authentication: PASS
✓ CIA1 Model: PASS
✓ CWRU Model: PASS
✓ NASA Model: PASS
✓ Induction Motor Model: PASS
✓ Comprehensive Diagnosis: PASS

TEST SUMMARY
============
Total Tests: 8
Passed: 8
Failed: 0
Success Rate: 100.0%
```

---

## File Organization Details

### Server Setup (`server_setup/`)
**Purpose**: Contains everything needed to start and configure the API server

Files:
- `backend/` - FastAPI application source code
- `deployment_config.json` - Configuration for which models to load
- `START_API_SERVER.bat` - Windows batch startup script
- `START_API_SERVER.ps1` - PowerShell startup script
- `requirements.txt` - Backend dependencies

### Server Testing (`server_testing/`)
**Purpose**: Contains all API testing and validation code

Directories:
- `api_tests/` - API endpoint tests
  - `test_all_models.py` - ⭐ Main comprehensive test suite
  - `test_api_simple.py` - Simple endpoint tests
  - `test_api_key_auth.py` - Authentication tests
- `logs/` - Test result logs and reports

### Utility Scripts (`utility_scripts/`)
**Purpose**: Helper scripts for debugging and maintenance

Common scripts:
- `diagnose_server.py` - Diagnose server issues
- `debug_registry.py` - Debug model registry loading
- `test_imports.py` - Test Python imports

---

## API Endpoints

All endpoints require authentication token from `/api/v1/auth/token`

```
Base URL: http://localhost:8002

Health & Status:
  GET  /health                          - Health check
  GET  /api/v1/models                   - List loaded models

Authentication:
  POST /api/v1/auth/token               - Get access token

Model Predictions:
  POST /api/v1/predict/cia1             - CIA-1 failure prediction
  POST /api/v1/predict/cwru             - Bearing fault location
  POST /api/v1/predict/nasa             - RUL prediction
  POST /api/v1/predict/induction        - Motor health status
  POST /api/v1/predict/current          - Electrical fault analysis
  POST /api/v1/predict/thermal          - Thermal image analysis

Comprehensive:
  POST /api/v1/diagnose/comprehensive   - Combined analysis
```

---

## Troubleshooting

### Issue: Models not loading
**Solution**: Check `server_setup/backend/deployment_config.json` paths

```bash
python utility_scripts/debug_registry.py
```

### Issue: Thermal model fails to load
**Status**: Fixed with safe_mode=False in model_registry.py

### Issue: Port 8002 already in use
**Solution**:
```bash
# Find process on port 8002
netstat -ano | findstr :8002

# Kill process
taskkill /PID <PID> /F
```

### Issue: Virtual environment error
**Solution**:
```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Default Credentials

```
Username: admin
Password: admin123
```

⚠️ Change these in production!

---

## Testing Models

### 1. Quick Health Check
```bash
curl http://localhost:8002/health
```

### 2. List Loaded Models
```bash
curl http://localhost:8002/api/v1/models
```

### 3. Full Test Suite
```bash
cd server_testing\api_tests
python test_all_models.py
```

---

## Next Steps

1. ✅ **Start Server**: Run `server_setup/START_API_SERVER.bat`
2. ✅ **Test API**: Run `server_testing/api_tests/test_all_models.py`
3. 📊 **Check Results**: Review test output for any failures
4. 🔧 **Troubleshoot**: Use utility scripts if needed
5. 🚀 **Deploy**: Follow `docs/technical_roadmap_v1.md`

---

## Model Status

| Model | Path | Status | Notes |
|-------|------|--------|-------|
| CIA-1 | `Trained_models/cia1_dl/best_mlp_model.keras` | ✅ Working | Production ready |
| NASA | `Trained_models/nasa_dl_comparison/Bi-LSTM-Attn/` | ✅ Working | With scaler |
| CWRU | `Trained_models/cwru_cnn/cnn_classifier.h5` | ✅ Working | Bearing faults |
| Induction | `Trained_models/induction_dl/best_cnn_model.keras` | ✅ Working | Motor health |
| Current Sig | `Trained_models/current_signature_dl/cnn_model.keras` | ✅ Working | Electrical faults |
| Thermal | `models/thermal/model.keras` | ✅ Fixed | Resolved deserialization |

---

*Last Updated: February 12, 2026*
*Project: Predictive Maintenance Digital Twin with MATLAB Integration*
