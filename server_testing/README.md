# Server Testing & API Validation

## Overview

This folder contains comprehensive test suites for validating the Predictive Maintenance API.

## Quick Start

```bash
# Run professional test
python run_api_test.py

# Expected: All 6 models tested across 4 conditions with detailed metrics
# Output: JSON report + console results
# Time: 5-10 minutes (includes server startup)
```

## Test Files

### `test_api_professional.py` ⭐ MAIN TEST
**Purpose**: Comprehensive system validation with professional reporting

**What it tests**:
- ✓ System validation (Python version, config)
- ✓ Server initialization (startup sequence)
- ✓ Health check endpoint
- ✓ Model loading (all 6 models)
- ✓ Authentication (OAuth2)
- ✓ Diagnosis tests (4 conditions: healthy, degradation, fault, critical)
- ✓ Performance metrics (response times)
- ✓ Model accuracy (per-model predictions)

**Output**:
- Console: Color-coded results with progress bar
- File: `api_test_report_YYYYMMDD_HHMMSS.json` (detailed data)

**Duration**: 5-10 minutes (first run includes 30-60s server startup)

### `test_all_models.py` 
**Purpose**: Verify all 6 models load correctly

**Tests**:
- Model availability
- File path validation
- Custom objects loading (Attention layer)
- Scaler availability

### `test_api_simple.py`
**Purpose**: Quick API validation

**Tests**:
- Health endpoint
- Basic diagnosis
- Auth endpoints

## Running Tests

### Option 1: Quick Test (5 minutes)
```bash
python tests/smoke/quick_test.py
```

### Option 2: Professional Test (10 minutes) ⭐ RECOMMENDED
```bash
python run_api_test.py
```

### Option 3: Full Pytest Suite (20-30 minutes)
```bash
pytest tests/ -v
```

### Option 4: Performance Test
```bash
pytest tests/performance/ -v
```

## Understanding Results

### Success Indicators
- ✅ All tests passed
- ✅ Success rate >= 90%
- ✅ Response times < 3 seconds
- ✅ All 6 models loaded

### Console Output Example
```
╔════════════════════════════════════════════════╗
║  PREDICTIVE MAINTENANCE API TEST SUITE        ║
║  Professional Performance & Validation Report ║
╚════════════════════════════════════════════════╝

✓ SYSTEM VALIDATION
  ✓ Python Version: 3.12.4
  ✓ API Server: http://localhost:8002
  ✓ Authentication: admin:***
  ✓ Model Timeout: 180s

⚙ SERVER INITIALIZATION
  ℹ Project Root: d:\...\Matlab_Project codes
  ℹ Backend Directory: ...backend
  ℹ Status: Starting server subprocess...
  Loading: [████████░░░░░░░░░░░░░░░░░░] 25% (45/180s)
  ✓ Server Health: ACTIVE
  ✓ Models Loaded: 6/6 READY

1️⃣ TEST 1: HEALTH CHECK
  ✓ Server Health: HEALTHY [2.45ms]

2️⃣ TEST 2: MODEL VERIFICATION
  ✓ CIA1
  ✓ CWRU
  ✓ Current_Signature
  ✓ Induction_Motor
  ✓ NASA
  ✓ Thermal

3️⃣ TEST 3: AUTHENTICATION
  ℹ Username: admin
  ✓ Authentication: SUCCESS [142.31ms]
  ℹ Token expires in: 60 minutes (3600s)

4️⃣ TEST 4: HEALTHY OPERATION
  ✓ Diagnosis Result: SUCCESS [2,234.56ms]
  • RUL (Hours): 1250.5
  • Health Status: Healthy
  • Confidence: 89.2%
  • Faults Detected: 0
  
  Model Predictions:
    • CIA1: RUL 1251h, Confidence 88.5%
    • ...

📊 TEST EXECUTION SUMMARY
====================================
Test Statistics:
  Total Tests Run: 12
  Tests Passed: ✓ 12
  Tests Failed: ✗ 0
  Success Rate: 100.0%

Performance Metrics (Response Times):
  Test Name                          Response Time
  healthy_diagnosis                  2,234.56 ms ✓
  degradation_diagnosis              2,156.34 ms ✓
  fault_diagnosis                    2,312.45 ms ⚠
  critical_diagnosis                 2,456.78 ms ⚠
  ────────────────────────────────────────────
  Average                            2,290.28 ms

Overall Status:
  ✓ PASSED - System is operational
```

### JSON Report Structure
```json
{
  "timestamp": "2026-02-12T16:15:30.123456",
  "summary": {
    "total_tests": 12,
    "passed": 12,
    "success_rate": 100.0,
    "status": "PASSED"
  },
  "performance": {
    "health_check": 2.45,
    "authentication": 142.31,
    "diagnosis_healthy": 2234.56,
    ...
  },
  "tests": {
    "models": {
      "count": 6,
      "models": ["CIA1", "CWRU", ...]
    },
    "diagnosis": {
      "healthy": {
        "rul": 1250.5,
        "health": "Healthy",
        "confidence": 89.2,
        "faults": 0,
        ...
      }
    }
  }
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Server failed to start" | Check port 8002, increase timeout to 180s |
| "Models not loading" | Verify model paths in `deployment_config.json` |
| "Tests timeout" | First run takes longer; check logs |
| "Connection refused" | Ensure server started before running test |

## Expected Performance

### Server Startup Times
- First run: 30-60 seconds (TensorFlow initialization)
- Subsequent: 10-20 seconds (models cached)

### Diagnosis Times  
- Healthy: ~2.2 seconds
- Degradation: ~2.1 seconds
- Fault: ~2.3 seconds
- Critical: ~2.4 seconds

### Model Accuracy (Expected)
- Healthy detection: >99%
- Fault detection: >85%
- RUL error: <10% (within 10 hours)

## References

- API Documentation: [../../docs/api/API_REFERENCE.md](../../docs/api/API_REFERENCE.md)
- Model Details: [../../docs/models/MODEL_ARCHITECTURE.md](../../docs/models/MODEL_ARCHITECTURE.md)
- Setup Guide: [../../docs/SETUP.md](../../docs/SETUP.md)

---

**Status**: ✅ Production Ready  
**Last Updated**: February 12, 2026
