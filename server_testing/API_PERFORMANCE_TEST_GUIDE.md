# 🚀 Comprehensive API Performance Test Guide

## Overview

The new test script (`test_api_with_server_auto_start.py`) provides comprehensive API testing with:

- ✅ **Automatic Server Start** - No need to start the server manually
- ✅ **Realistic Signals** - Tests with synthetic sensor data mimicking real conditions
- ✅ **Multiple Scenarios** - Tests healthy, degrading, and critical conditions
- ✅ **Performance Metrics** - Measures response times and prediction accuracy
- ✅ **Detailed Reports** - Saves results to JSON for analysis
- ✅ **Authentication** - Tests the full auth system
- ✅ **All Models** - Verifies all 6 models are loaded and working

---

## Quick Start

### Run the Test
```bash
python run_api_test.py
```

That's it! The script will:
1. Launch the API server
2. Load all 6 models
3. Authenticate
4. Run comprehensive tests
5. Display performance analysis
6. Save detailed results

### Expected Runtime
- **Server startup**: 30-60 seconds (loading 6 models)
- **Tests**: 2-5 minutes
- **Total**: 5-10 minutes

---

## What Gets Tested

### 1. **Health Check**
- Verifies server is running
- Measures response time
- Checks system status

### 2. **Models Loaded**
- Verifies all 6 models are loaded:
  - CIA1 (Machine failure prediction)
  - NASA (RUL prediction)
  - CWRU (Bearing faults)
  - Induction Motor (Motor health)
  - Current Signature (Electrical faults)
  - Thermal (Image analysis)

### 3. **Authentication**
- Tests login with credentials
- Obtains authorization token
- Verifies token expiration settings

### 4. **Diagnosis with Different Conditions**

The script generates 4 different signal conditions:

#### **HEALTHY**
- Normal baseline signal
- Low noise levels
- No fault indicators
```
Expected: Healthy status, High RUL, No faults
```

#### **EARLY DEGRADATION**
- Increased harmonic content
- More noise
- Early warning signs
```
Expected: Warning status, Medium RUL, Maybe minor faults
```

#### **FAULT DEVELOPING**
- Strong harmonics
- Impulsive noise (bearing defects)
- Clear fault signatures
```
Expected: Alert status, Lower RUL, Detected faults
```

#### **CRITICAL**
- Very strong abnormal signals
- Heavy impulsive content
- Multiple fault indicators
```
Expected: Critical status, Very low RUL, Multiple faults
```

---

## Output Examples

### Console Output

```
================================================================================
                    PREDICTIVE MAINTENANCE API
           Comprehensive Performance Test with Auto Server
================================================================================

→ STARTING API SERVER
────────────────────────────────────────────────────────────────────────────────
Project Root: D:\Your\Project\Path
Backend Dir: D:\Your\Project\Path\backend
ℹ Waiting for server to start...
✓ API Server started successfully

→ TEST 1: Health Check
────────────────────────────────────────────────────────────────────────────────
✓ Server health: healthy (0.015s)

→ TEST 2: Models Loaded
────────────────────────────────────────────────────────────────────────────────
ℹ Loaded Models (6):
✓ CIA1
✓ CWRU
✓ Current_Signature
✓ Induction_Motor
✓ NASA
✓ Thermal

→ TEST 3: Authentication
────────────────────────────────────────────────────────────────────────────────
Logging in: admin
✓ Authentication successful (0.245s)
ℹ Token expires in: 3600 seconds (60 minutes)

→ TEST: Comprehensive Diagnosis - HEALTHY
────────────────────────────────────────────────────────────────────────────────
Generating healthy signal...
  Vibration - Mean: 0.0012, Std: 0.5234, Max: 2.1456
Sending diagnosis request...
Response received in 2.34s

✓ Diagnosis successful (2.342s)

Diagnostic Results:
  RUL: 1250.5 hours (confidence: 89.2%)
  Health: Healthy
  Action: Continue normal operation

Detected Faults (0):
    (No faults detected)

→ TEST: Comprehensive Diagnosis - EARLY_DEGRADATION
────────────────────────────────────────────────────────────────────────────────
...

================================================================================
                           PERFORMANCE ANALYSIS
================================================================================

Response Times:
  health_check...................................... 0.015s
  authentication.................................... 0.245s
  diagnosis_healthy................................. 2.342s
  diagnosis_early_degradation........................ 2.156s
  diagnosis_fault_developing......................... 2.289s
  diagnosis_critical................................. 2.401s

Model Predictions Summary:

  HEALTHY
    RUL: 1250.5h (confidence: 89.2%)
    Health: Healthy
    Faults: 0
    Time: 2.34s

  EARLY_DEGRADATION
    RUL: 856.2h (confidence: 82.1%)
    Health: Warning
    Faults: 1
    Time: 2.16s

  FAULT_DEVELOPING
    RUL: 245.8h (confidence: 91.5%)
    Health: Alert
    Faults: 2
    Time: 2.29s

  CRITICAL
    RUL: 45.3h (confidence: 94.2%)
    Health: Critical
    Faults: 3
    Time: 2.40s

✓ Results saved to: api_performance_test_20260212_102533.json
```

### JSON Report Example

The script saves a detailed JSON report:

```json
{
  "timestamp": "2026-02-12T10:25:33.456789",
  "tests": {
    "models_loaded": {
      "count": 6,
      "models": [
        "CIA1",
        "CWRU",
        "Current_Signature",
        "Induction_Motor",
        "NASA",
        "Thermal"
      ]
    },
    "authentication": {
      "status": "success",
      "expires_in": 3600
    }
  },
  "performance": {
    "health_check": 0.015,
    "authentication": 0.245,
    "diagnosis_healthy": 2.342,
    "diagnosis_early_degradation": 2.156,
    "diagnosis_fault_developing": 2.289,
    "diagnosis_critical": 2.401
  },
  "model_predictions": {
    "healthy": {
      "rul_hours": 1250.5,
      "rul_confidence": 0.892,
      "overall_health": "Healthy",
      "priority_action": "Continue normal operation",
      "faults_detected": 0,
      "execution_time": 2.342
    },
    "early_degradation": {
      "rul_hours": 856.2,
      "rul_confidence": 0.821,
      "overall_health": "Warning",
      "priority_action": "Monitor closely",
      "faults_detected": 1,
      "execution_time": 2.156
    },
    ...
  }
}
```

---

## Understanding the Results

### 1. **Response Times**
Shows how fast the API responds:
- ✅ **< 1s**: Excellent
- ✅ **1-3s**: Good
- ⚠️ **3-5s**: Acceptable
- ❌ **> 5s**: Slow

### 2. **RUL (Remaining Useful Life)**
- Measured in hours
- Indicates time until failure
- Higher confidence = more reliable prediction

### 3. **Health Status**
- **Healthy**: No issues detected
- **Warning**: Early signs of degradation
- **Alert**: Faults developing
- **Critical**: Urgent maintenance needed

### 4. **Confidence Levels**
- **90-100%**: High confidence
- **80-90%**: Good confidence
- **70-80%**: Medium confidence
- **< 70%**: Low confidence

### 5. **Detected Faults**
- Component name (e.g., "Bearing")
- Fault type (e.g., "Outer Race")
- Severity level
- Confidence percentage

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Script not found** | Make sure you're in project root directory |
| **Server won't start** | Check if port 8002 is already in use |
| **Tests timeout** | Server may be slow loading models (wait longer) |
| **Connection refused** | Server failed to start - check logs |
| **Auth fails** | Credentials may have changed |

---

## Alternative Methods to Run

### Method 1: Direct Run (Recommended)
```bash
python run_api_test.py
```

### Method 2: Direct Script
```bash
cd server_testing/api_tests
python test_api_with_server_auto_start.py
```

### Method 3: Manual + Test
```bash
# Terminal 1
python start_api_server.py

# Terminal 2 (when "Application startup complete" appears)
cd server_testing/api_tests
python test_api_with_server_auto_start.py
```

---

## What Each Signal Represents

### Vibration Signal Features

| Feature | Healthy | Degradation | Fault | Critical |
|---------|---------|-------------|-------|----------|
| **Base frequency** | 60 Hz | 60 Hz | 60 Hz | 60 Hz |
| **Harmonics** | Low (120Hz) | Medium (120Hz, 180Hz) | Strong (120/180/240Hz) | Very Strong (up to 300Hz) |
| **Noise level** | Low (±0.05) | Medium (±0.1) | High (±0.15) | Very High (±0.2) |
| **Impulses** | None | None | Occasional | Frequent |
| **Signal chaos** | Very low | Low | Medium | High |

### Current Signal
- **Phases**: 3-phase balanced current
- **Frequency**: 50 Hz
- **Magnitude**: 5.0 Amps
- **Noise**: Added based on condition

---

## Performance Expectations

### Typical Results

| Condition | RUL (hours) | Confidence | Health | Faults |
|-----------|-------------|------------|--------|--------|
| Healthy | 800-1500 | 85-95% | Healthy | 0 |
| Early Degradation | 500-900 | 75-90% | Warning | 0-2 |
| Fault Developing | 100-500 | 80-95% | Alert | 1-3 |
| Critical | 10-100 | 90-98% | Critical | 2-5 |

---

## Interpreting Model Performance

### ✅ Good Performance Indicators
- RUL predictions correlate with signal condition
- Confidence increases with problem severity
- Health status matches signal characteristics
- Response times consistent (< 3s)
- All models contribute to diagnosis

### ⚠️ Watch For
- Very high confidence with unusual predictions
- Inconsistent results across conditions
- Slow response times (> 5s)
- Models not contributing equally

---

## Next Steps After Testing

1. **Review Results**: Check the generated JSON report
2. **Analyze Performance**: Look for patterns in predictions
3. **Validate**: Do the predictions make sense?
4. **Integrate**: Use API in your MATLAB or application
5. **Monitor**: Track performance over time

---

## Additional Information

- **Credentials**: admin / admin123 (default)
- **Server Port**: 8002
- **Auth Token Expiry**: 1 hour
- **Test Duration**: 5-10 minutes
- **Report Format**: JSON (machine-readable)

---

## Support

If you encounter issues:

1. **Check logs** - Check console output for error messages
2. **Verify models** - Run `python utility_scripts/diagnose_api_setup.py`
3. **Manual test** - Try running server and test separately
4. **Check port** - Ensure 8002 is free: `netstat -ano | findstr :8002`

---

**Ready to test?**

```bash
python run_api_test.py
```

That's all you need! 🚀

*Last Updated: February 12, 2026*
