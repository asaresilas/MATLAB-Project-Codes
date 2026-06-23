# 📚 COMPREHENSIVE API TEST RESOURCES

## 🚀 QUICK START (Pick One)

### **Easiest**: One Command to Test Everything
```bash
python run_api_test.py
```
✅ Starts server automatically  
✅ Tests all models with realistic signals  
✅ Generates report  
✅ See [RUN_API_TEST_NOW.md](RUN_API_TEST_NOW.md)

### **Manual**: Step-by-Step
```bash
# Terminal 1: Start server
python start_api_server.py

# Terminal 2: Run tests (after "Application startup complete")
cd server_testing/api_tests
python test_api_with_server_auto_start.py
```
✅ More control  
✅ See what's happening  
✅ Easier debugging

---

## 📖 DOCUMENTATION FILES

| File | Purpose | Read Time |
|------|---------|-----------|
| **RUN_API_TEST_NOW.md** ⭐ | Quick start - what to expect | 3 min |
| **API_PERFORMANCE_TEST_GUIDE.md** | Detailed test explanation | 15 min |
| **QUICK_START.md** | General quick start | 5 min |
| **PROJECT_ORGANIZATION.md** | Full reference | 15 min |

---

## 🧪 TEST SCRIPTS

### Main Test Scripts

| Script | Purpose | How to Run |
|--------|---------|-----------|
| **test_api_with_server_auto_start.py** | Comprehensive tests with auto server start | `python run_api_test.py` |
| **test_all_models.py** | Simple model validation | `python test_all_models.py` |
| **test_api_simple.py** | Basic endpoint tests | `python test_api_simple.py` |

### Launcher Scripts

| Script | Purpose |
|--------|---------|
| **run_api_test.py** | Main launcher (easiest!) |
| **start_api_server.py** | Start server only |
| **server_setup/START_API_SERVER.bat** | Windows batch starter |
| **server_setup/START_API_SERVER.ps1** | PowerShell starter |

---

## 🎯 WHAT GETS TESTED

### Test Suite Coverage

1. **Server Health**
   - Is API running?
   - Response time?

2. **Models Loaded**
   - CIA1 (Predictive Maintenance)
   - NASA (RUL Prediction)
   - CWRU (Bearing Faults)
   - Induction Motor (Motor Health)
   - Current Signature (Electrical)
   - Thermal (Image Analysis)

3. **Authentication**
   - Login with credentials
   - Token generation
   - Token expiration

4. **Realistic Signal Testing** (Our New Feature!)
   - **Healthy Condition**: ~1250 RUL, 0 faults
   - **Early Degradation**: ~850 RUL, 1 fault
   - **Fault Developing**: ~250 RUL, 2-3 faults
   - **Critical**: ~50 RUL, 3+ faults

5. **Performance Metrics**
   - Response times
   - Prediction confidence
   - RUL accuracy
   - Fault detection

---

## 📊 SIGNAL GENERATION

### What the Test Creates

#### **Healthy Signal**
```
Base: 60Hz sine wave
Harmonics: Weak 120Hz
Noise: Low (±0.05)
Impulses: None
Expected RUL: 800-1500 hours
Expected Faults: 0
```

#### **Early Degradation**
```
Base: 60Hz sine wave
Harmonics: Medium 120Hz + 180Hz
Noise: Medium (±0.1)
Impulses: Rare
Expected RUL: 500-900 hours
Expected Faults: 0-2
```

#### **Fault Developing**
```
Base: 60Hz sine wave
Harmonics: Strong 120Hz + 180Hz + 240Hz
Noise: High (±0.15)
Impulses: Occasional (bearing defects)
Expected RUL: 100-500 hours
Expected Faults: 1-3
```

#### **Critical**
```
Base: 60Hz sine wave
Harmonics: Very strong 120Hz-300Hz
Noise: Very high (±0.2)
Impulses: Frequent (heavy defects)
Expected RUL: 10-100 hours
Expected Faults: 2-5
```

---

## 🔄 TEST FLOW

```
START
  │
  ├─→ [Auto Server Start]
  │     ├─ Launch subprocess
  │     ├─ Wait for /health endpoint
  │     └─ Confirm "Application startup complete"
  │
  ├─→ [Health Check]
  │     └─ Verify server is running (< 1s)
  │
  ├─→ [Load Models Verification]
  │     └─ Confirm all 6 models loaded
  │
  ├─→ [Authentication]
  │     └─ Get bearer token
  │
  ├─→ [Test 4 Signal Conditions]
  │     ├─ Generate healthy signal
  │     ├─ Send to /diagnose/comprehensive
  │     ├─ Collect results & timing
  │     │
  │     ├─ Generate degradation signal
  │     ├─ Send to /diagnose/comprehensive
  │     ├─ Collect results & timing
  │     │
  │     ├─ Generate fault signal
  │     ├─ Send to /diagnose/comprehensive
  │     ├─ Collect results & timing
  │     │
  │     └─ Generate critical signal
  │         ├─ Send to /diagnose/comprehensive
  │         └─ Collect results & timing
  │
  ├─→ [Analysis]
  │     ├─ Calculate average response times
  │     ├─ Verify prediction progression
  │     └─ Assess confidence levels
  │
  ├─→ [Report generation]
  │     ├─ Console output (formatted)
  │     ├─ JSON file (detailed)
  │     └─ Performance summary
  │
  └─→ [Cleanup]
        ├─ Stop server
        └─ Exit
```

---

## 📈 EXPECTED OUTPUTS

### Console Output Structure
```
HEADER
  ↓
SERVER STARTUP (30-60 sec)
  ↓
TEST 1: Health Check (< 1 sec)
  ↓
TEST 2: Models Loaded (< 1 sec)
  ↓
TEST 3: Authentication (< 1 sec)
  ↓
TEST 4.1: Healthy Signal (2-3 sec)
  ↓
TEST 4.2: Degradation Signal (2-3 sec)
  ↓
TEST 4.3: Fault Signal (2-3 sec)
  ↓
TEST 4.4: Critical Signal (2-3 sec)
  ↓
PERFORMANCE ANALYSIS
  ↓
SUMMARY
  ↓
CLEANUP & REPORT
```

### JSON Report Structure
```json
{
  "timestamp": "ISO format",
  "tests": {
    "models_loaded": {...},
    "authentication": {...}
  },
  "performance": {
    "health_check": 0.015,
    "authentication": 0.245,
    "diagnosis_*": 2.3
  },
  "model_predictions": {
    "healthy": {
      "rul_hours": 1250.5,
      "rul_confidence": 0.892,
      "overall_health": "Healthy",
      "faults_detected": 0,
      "execution_time": 2.342
    },
    ...
  }
}
```

---

## 🎓 HOW TO INTERPRET RESULTS

### RUL Progression (With Different Signals)
```
Healthy:         1250 hours ✅ - Very good
Degradation:      850 hours ⚠️ - Getting worse
Fault:            250 hours ⚠️ - Concerning
Critical:          45 hours ❌ - Urgent
```

### Health Status Progression
```
Healthy         ← Normal operation
    ↓
Warning         ← Early signs
    ↓
Alert           ← Clear problems
    ↓
Critical        ← Immediate action needed
```

### Confidence Progression
```
Should INCREASE with problem severity
Healthy:        85-90% (lower confidence = normal signal)
Degradation:    80-85% (moderate)
Fault:          85-95% (high confidence in fault detection)
Critical:       90-98% (very high confidence in critical state)
```

---

## 🔍 VALIDATION CHECKLIST

After running test, verify:

- [ ] Server started successfully
- [ ] All 6 models loaded
- [ ] Authentication worked
- [ ] All 4 signal tests completed
- [ ] Response times < 3 seconds
- [ ] RUL decreases with severity
- [ ] Faults increase with severity
- [ ] Confidence is consistent
- [ ] JSON report generated
- [ ] No errors in console

---

## 🛠️ CUSTOMIZATION

To modify the test (advanced):

1. **Change signal parameters**: Edit `generate_signals()` function
2. **Add new test conditions**: Add to `conditions` list
3. **Modify signal generation**: Adjust frequency, noise, impulses
4. **Change API parameters**: Modify temperature, speed values
5. **Adjust timeouts**: Change `SERVER_STARTUP_TIMEOUT`

---

## 📞 SUPPORT PATHS

**Is the test..?**

- **Not running**: Check [QUICK_START.md](QUICK_START.md)
- **Timing out**: Server may be slow (first run takes time)
- **Failing auth**: Verify credentials (admin/admin123)
- **Models not loading**: Run `diagnose_api_setup.py`
- **Port in use**: Kill process on 8002

---

## 🎯 SUMMARY

| Need | File/Script |
|------|------------|
| **Run everything in one command** | `python run_api_test.py` |
| **Quick start guide** | [RUN_API_TEST_NOW.md](RUN_API_TEST_NOW.md) |
| **Detailed test explanation** | [API_PERFORMANCE_TEST_GUIDE.md](API_PERFORMANCE_TEST_GUIDE.md) |
| **Manual step-by-step** | [QUICK_START.md](../QUICK_START.md) |
| **Verify setup** | `python ../utility_scripts/diagnose_api_setup.py` |

---

## ⚡ TL;DR

```bash
python run_api_test.py
```

Wait 5-10 minutes, you'll see:
- ✅ Server starts
- ✅ All 6 models load
- ✅ Authentication works
- ✅ Tests run with 4 signal conditions
- ✅ Performance analysis displayed
- ✅ JSON report saved

Done! 🎉

---

*All test infrastructure deployed and documented - February 12, 2026*
