# API Testing Guide

## Quick Start

### Prerequisites
- Python 3.9+ installed
- Virtual environment activated: `.venv`
- API server running on http://localhost:8002

### Run Tests

```bash
# From server_testing/api_tests/
python test_all_models.py
```

Output:
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
Passed: 8/8 (100%)
```

---

## What Gets Tested

| Test | Endpoint | Purpose | Status |
|------|----------|---------|--------|
| Health Check | `GET /health` | Verify server is running | Should PASS immediately |
| Models Endpoint | `GET /api/v1/models` | Verify all 6 models loaded | Should list CIA1, NASA, CWRU, etc. |
| Authentication | `POST /api/v1/auth/token` | Verify authentication works | Should return access token |
| CIA-1 Model | `POST /api/v1/predict/cia1` | Test machine failure prediction | Should return prediction |
| CWRU Model | `POST /api/v1/predict/cwru` | Test bearing fault detection | Should identify fault type |
| NASA Model | `POST /api/v1/predict/nasa` | Test RUL (Remaining Useful Life) | Should return hours remaining |
| Induction Motor | `POST /api/v1/predict/induction` | Test motor health status | Should return health status |
| Comprehensive | `POST /api/v1/diagnose/comprehensive` | Test all models combined | Should return detailed analysis |

---

## Results

Test results are automatically saved to:
```
server_testing/api_tests/api_test_results_YYYYMMDD_HHMMSS.json
```

Example result:
```json
{
  "timestamp": "2026-02-12T10:30:45.123456",
  "url": "http://localhost:8002",
  "tests": {
    "Health Check": {
      "status": "PASS",
      "details": "Status: healthy"
    },
    "Models Endpoint": {
      "status": "PASS",
      "details": "Loaded: 6/6 models - CIA1, CWRU, Current_Signature, Induction_Motor, NASA, Thermal"
    }
  },
  "summary": {
    "total": 8,
    "passed": 8,
    "failed": 0,
    "success_rate": "100.0%"
  }
}
```

---

## Troubleshooting

### Test Fails: "Connection refused"
**Cause**: API server not running
**Solution**: Start server with `server_setup/START_API_SERVER.bat`

### Test Fails: "Models Endpoint: PARTIAL"
**Cause**: One or more models failed to load
**Solution**: Check `server_testing/logs/` for error messages

### Models not loading
Check model paths in `server_setup/backend/deployment_config.json`:
```json
{
  "CIA1": {
    "model_path": "Trained_models/cia1_dl/best_mlp_model.keras",
    ...
  }
}
```

All paths must be relative to project root.

---

## Advanced Testing

### Test specific endpoint
```bash
python test_all_models.py http://localhost:8002
```

### Test with custom API URL
```bash
python test_all_models.py http://192.168.1.100:8002
```

---

## Models & Endpoints

### 1. CIA-1 (Predictive Maintenance)
- **Endpoint**: `POST /api/v1/predict/cia1`
- **Input**: Machine parameters (temperature, RPM, torque, tool wear)
- **Output**: Failure prediction (True/False)

### 2. CWRU (Bearing Faults)
- **Endpoint**: `POST /api/v1/predict/cwru`
- **Input**: Vibration signal (1000 samples)
- **Output**: Fault type (Normal, Inner Race, Ball, Outer Race)

### 3. NASA (RUL)
- **Endpoint**: `POST /api/v1/predict/nasa`
- **Input**: Features (9-dimensional)
- **Output**: RUL hours, Confidence

### 4. Induction Motor
- **Endpoint**: `POST /api/v1/predict/induction`
- **Input**: Vibration signal
- **Output**: Health status

### 5. Current Signature
- **Endpoint**: `POST /api/v1/predict/current`
- **Input**: 3-phase current data
- **Output**: Electrical fault analysis

### 6. Thermal
- **Endpoint**: `POST /api/v1/predict/thermal`
- **Input**: Thermal image (base64)
- **Output**: Thermal diagnosis

---

## Authentication

Default credentials:
```
Username: admin
Password: admin123
```

To authenticate:
```bash
curl -X POST "http://localhost:8002/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Manual API Testing

### 1. Health Check
```bash
curl http://localhost:8002/health
```

### 2. List Models
```bash
curl http://localhost:8002/api/v1/models
```

Response:
```json
{
  "loaded_models": ["CIA1", "NASA", "CWRU", "Induction_Motor", "Current_Signature", "Thermal"],
  "configs": { ... }
}
```

### 3. Get Token
```bash
curl -X POST "http://localhost:8002/api/v1/auth/token" \
  -d "username=admin&password=admin123"
```

### 4. Make Prediction
```bash
curl -X POST "http://localhost:8002/api/v1/predict/cia1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"air_temperature": 298, "process_temperature": 308, "rpm": 1500, "torque": 40, "tool_wear": 0, "type": "M"}'
```

---

## Expected Results

All tests should show:
- ✓ Health Check: PASS
- ✓ Models Endpoint: PASS
- ✓ Authentication: PASS
- ✓ All 6 Models: PASS
- ✓ Comprehensive Diagnosis: PASS

**Success Rate: 100%**

If any test fails, check:
1. API server is running
2. All models are in correct paths
3. Port 8002 is not blocked
4. Virtual environment is activated

---

*Last Updated: February 12, 2026*
