# 🚀 MATLAB INTEGRATION - QUICK START GUIDE

**Document**: Implementation Quick Reference  
**Target Duration**: 6 weeks  
**Team Size**: 2-3 developers + 1 DevOps  

---

## 📊 OVERVIEW AT A GLANCE

### Architecture
```
MATLAB/Simulink ←→ WebSocket ←→ FastAPI Server ←→ TensorFlow Models
(Virtual System)  (Real-time)  (Prediction)     (Deep MLP, 1D CNN, etc)
                                   ↓
                            PostgreSQL Database
                            (Persistent Storage)
                                   ↓
                            Weekly Retraining
                            (Continuous Learning)
```

### Performance Targets
| Component | Target |
|-----------|--------|
| API Latency | <50ms (P95) |
| Throughput | 1000 msg/sec |
| Uptime | 99.5% |
| Accuracy | >94% |
| Retraining | Weekly |

---

## 🔌 COMMUNICATION: WEBSOCKET VS REST

### Choose WebSocket If:
- ✅ Continuous real-time streaming from Simulink
- ✅ Need <20ms latency
- ✅ Want server to push updates to MATLAB
- ✅ Have 10+ concurrent MATLAB instances

### Choose REST If:
- ✅ Occasional predictions (not streaming)
- ✅ Latency <100ms acceptable
- ✅ MATLAB version doesn't support WebSocket
- ✅ Simple HTTP integration preferred

**RECOMMENDATION**: Use **WebSocket** for production real-time learning system

---

## 💻 IMPLEMENTATION CHECKLIST

### [ ] Week 1: Core Communication
- [ ] WebSocket endpoint in `backend/app/websocket_handler.py`
  ```python
  @app.websocket("/ws/simulink/{client_id}")
  async def websocket_endpoint(websocket: WebSocket, client_id: str):
      # Receive sensor data from MATLAB
      # Process through model
      # Send prediction back
  ```

- [ ] MATLAB client class: `matlab_client/PredictiveMaintenanceClient.m`
  ```matlab
  pm_client = PredictiveMaintenanceClient('http://localhost:8002', 'simulink_1');
  pm_client.connect();
  prediction = pm_client.predict(sensor_values);
  ```

- [ ] Test basic connectivity
  ```bash
  python servers/run_server.py  # Start API
  matlab tests/test_matlab_to_api.m  # Run MATLAB test
  ```

### [ ] Week 2: Prediction & Performance
- [ ] Fast prediction path (<20ms)
  ```python
  async def fast_predict(sensor_data):
      # Load Deep MLP model once
      # Batch inference if needed
      # Return immediately
  ```

- [ ] Fallback model system
  ```python
  # If Deep MLP fails → Use MLP backup
  # If both fail → Return error with graceful degradation
  ```

- [ ] Latency tracking
  ```python
  # Track every prediction latency
  # Log to database
  # Alert if P95 > 50ms
  ```

### [ ] Week 3: Data & Learning
- [ ] PostgreSQL schema
  ```sql
  CREATE TABLE sensor_readings (
      id SERIAL PRIMARY KEY,
      timestamp TIMESTAMP,
      simulink_session_id VARCHAR,
      sensor_values FLOAT8[14],
      ground_truth VARCHAR,
      created_at TIMESTAMP
  );
  
  CREATE TABLE predictions (
      id SERIAL PRIMARY KEY,
      sensor_reading_id INT,
      prediction_class VARCHAR,
      confidence FLOAT,
      latency_ms FLOAT,
      was_correct BOOLEAN,
      FOREIGN KEY (sensor_reading_id) REFERENCES sensor_readings(id)
  );
  
  CREATE TABLE model_versions (
      version_id VARCHAR PRIMARY KEY,
      training_date TIMESTAMP,
      accuracy FLOAT,
      status VARCHAR,
      file_path VARCHAR
  );
  ```

- [ ] Weekly retraining job
  ```python
  # Create: `scripts/training/retrain_weekly.py`
  # Trigger: Every Monday 2 AM
  # Process:
  #   1. Collect labeled data from past week
  #   2. Fine-tune Deep MLP on new data
  #   3. Validate accuracy
  #   4. A/B test with 10% traffic
  #   5. Promote if better after 2 weeks
  ```

- [ ] Ground truth collection
  ```matlab
  % In MATLAB when failure occurs:
  pm_client.send_ground_truth(
      prediction_timestamp,
      'bearing_outer_race_fault',
      45);  % actual hours to failure
  ```

### [ ] Week 4: Reliability
- [ ] Database backup system
  ```bash
  # Daily 2 AM: pg_dump → gzip → backup folder
  # Weekly: Copy to cloud storage
  # Monthly: Test restore
  ```

- [ ] Error handling & monitoring
  ```python
  # Health check endpoint
  @app.get("/health")
  async def health():
      return {
          "status": "healthy",
          "models_ready": True,
          "db_connected": True,
          "memory_mb": 450
      }
  ```

- [ ] Prometheus metrics
  ```python
  from prometheus_client import Counter, Histogram
  
  prediction_latency = Histogram('api_prediction_latency_ms', 'Latency')
  prediction_errors = Counter('api_prediction_errors', 'Errors')
  ```

### [ ] Week 5: Testing
- [ ] Unit tests
  ```bash
  pytest tests/unit/ -v
  ```

- [ ] Integration tests
  ```bash
  pytest tests/integration/ -v
  ```

- [ ] Load test (100 concurrent MATLAB clients)
  ```bash
  bash tests/load_test.sh
  ```

### [ ] Week 6: Deploy & Document
- [ ] Production deployment
  ```bash
  # Configure: servers/config/production.yaml
  # Deploy: ansible playbooks/deploy.yml
  # Verify: curl http://prod-server:8002/health
  ```

- [ ] Documentation
  - [ ] MATLAB Integration Guide: `docs/MATLAB_INTEGRATION_GUIDE.md`
  - [ ] API Endpoint Reference: `docs/api/API_REFERENCE.md`
  - [ ] Troubleshooting: `docs/TROUBLESHOOTING.md`

---

## 📁 FILE STRUCTURE

```
project_root/
├── backend/
│   └── app/
│       ├── main.py (main FastAPI app)
│       ├── websocket_handler.py ← NEW: WebSocket logic
│       ├── models_loader.py (load TensorFlow models)
│       ├── db_models.py (SQLAlchemy schemas)
│       └── services/
│           ├── predictor.py (inference logic)
│           ├── retrainer.py ← NEW: Weekly learning
│           └── drift_detector.py ← NEW: Anomaly detection
│
├── matlab_client/ ← NEW CLIENT CODE
│   ├── PredictiveMaintenanceClient.m (main MATLAB class)
│   ├── example_simulink_integration.slx (example model)
│   └── tests/
│       └── test_api_communication.m
│
├── scripts/
│   ├── training/
│   │   └── retrain_weekly.py ← NEW: Scheduled retraining
│   └── monitoring/
│       └── monitor_drift.py ← NEW: Detect concept drift
│
├── tests/
│   ├── unit/
│   │   ├── test_prediction_latency.py
│   │   └── test_fallback_models.py
│   ├── integration/
│   │   └── test_matlab_integration.py
│   └── load_test.sh
│
├── docs/
│   ├── MATLAB_INTEGRATION_PLAN.md (this file)
│   ├── MATLAB_INTEGRATION_GUIDE.md ← NEW: How-to guide
│   └── api/
│       └── WEBSOCKET_REFERENCE.md ← NEW: Protocol spec
│
└── deployment/
    ├── docker/
    │   ├── Dockerfile
    │   └── docker-compose.yml
    └── systemd/
        └── ml-api.service
```

---

## 🔧 QUICK SETUP (Local Development)

### 1. Start API Server
```bash
cd servers/
python run_server.py
# Output: "Application startup complete" (30-60 seconds)
```

### 2. Test WebSocket Connection (Python)
```python
import asyncio
import json
from websockets import connect

async def test():
    uri = "ws://localhost:8002/ws/simulink/test_client"
    async with connect(uri) as websocket:
        # Send sensor data
        msg = {"sensors": [25.3, 0.12, 1.2], "timestamp": "2026-02-12T16:00:00"}
        await websocket.send(json.dumps(msg))
        
        # Receive prediction
        response = json.loads(await websocket.recv())
        print(f"Prediction: {response['prediction']['class']}")
        print(f"Latency: {response['performance']['latency_ms']:.1f}ms")

asyncio.run(test())
```

### 3. Test with MATLAB
```matlab
pm_client = PredictiveMaintenanceClient('http://localhost:8002', 'test');
pm_client.connect();

sensor_data = randn(14, 1);  % Random sensor values
prediction = pm_client.predict(sensor_data);

disp(['Predicted: ' char(prediction.class)]);
disp(['Confidence: ' num2str(prediction.confidence * 100) '%']);
disp(['Latency: ' num2str(prediction.latency_ms) 'ms']);

pm_client.disconnect();
```

---

## 📊 PERFORMANCE TUNING

### Optimize Latency (<20ms target)
```python
# 1. Use model caching (load once at startup)
models = {
    'deep_mlp': load_model('best_model_Deep_MLP.keras'),
    'ensemble': load_model('best_model_Ensemble_NN.keras'),
}

# 2. Use batch predictions (if buffering possible)
async def batch_predict(data_buffer):
    if len(data_buffer) >= 10:
        predictions = model.predict_on_batch(data_buffer)
        return predictions

# 3. Use GPU acceleration
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
model = load_model(...)  # Automatically uses GPU if available

# 4. Profile to find bottlenecks
import cProfile
cProfile.run('predict(sensor_data)')
```

### Handle High Throughput (1000+ msg/sec)
```python
# 1. Use async/await for non-blocking I/O
# 2. Connection pooling for database
# 3. Message queue if volume exceeds capacity
#    └─ RabbitMQ or Redis queue as buffer
# 4. Load balance across multiple API instances
```

---

## 🔍 MONITORING DURING DEVELOPMENT

### Terminal 1: Start API Server
```bash
python servers/run_server.py
```

### Terminal 2: Watch Logs
```bash
tail -f logs/*.txt
```

### Terminal 3: Monitor Metrics (when deployed)
```bash
curl http://localhost:8002/metrics | grep prediction
# Output: prediction_latency_ms_bucket, prediction_errors_total, etc.
```

### Terminal 4: Run MATLAB Client
```matlab
pm_client = ...
for i = 1:100
    prediction = pm_client.predict(sensor_data);
    fprintf('%d: %.1fms\n', i, prediction.latency_ms);
end
```

---

## ⚠️ COMMON PITFALLS

| Pitfall | Solution |
|---------|----------|
| **WebSocket loses connection after 5 min** | Implement heartbeat/ping-pong: `await ws.send_json({"type": "ping"})` |
| **MATLAB hangs waiting for response** | Add timeout: `receive(ws, 5)` (5 second timeout) |
| **Predictions get slower over time** | Memory leak → Enable garbage collection or restart server daily |
| **Retraining fails silently** | Log to file with timestamp and error details |
| **Model accuracy drops after update** | Always A/B test new models before full rollout |
| **Database runs out of space** | Archive old data monthly: `DELETE FROM sensor_readings WHERE created_at < NOW() - interval '3 months'` |

---

## 🚨 FAILURE SCENARIOS & RECOVERY

### Scenario 1: API Server Crashes
```yaml
# Handled by: systemd auto-restart
Before: API down → MATLAB errors
After: systemd restarts in <5 seconds, MATLAB reconnects automatically
```

### Scenario 2: Model Loading Fails
```python
# Handled by: Fallback to previous version
If new model (v1.3) fails to load:
  → Automatically load v1.2 (known good)
  → Log error: "Model v1.3 loading failed, using v1.2"
  → Alert: "Model loading issue - investigate"
```

### Scenario 3: Database Connection Lost
```python
# Handled by: Connection pooling with auto-retry
If database unreachable:
  → Retry with exponential backoff (100ms → 1s → 10s)
  → Buffer data in memory temporarily
  → Once reconnected: flush buffer to database
  → Alert if offline >5 minutes
```

### Scenario 4: MATLAB Client Disconnects
```python
# Handled by: Graceful cleanup
If WebSocket drops:
  → Close connection cleanly
  → Save any partial data
  → Free connection resources
  → MATLAB can reconnect with new session ID
```

---

## 🎯 SUCCESS METRICS (After 1 Month in Production)

Check these metrics to confirm system is working:

```bash
# 1. Latency
Average latency: < 25 ms (target: <20ms)
P95 latency: < 50 ms (target: <50ms)

# 2. Accuracy  
Prediction accuracy: > 94% (baseline: 94.1%)
False negative rate: < 2% (safety critical)

# 3. Reliability
Server uptime: > 99.5% (52.56+ minutes per week)
Data loss: 0 records
Connection drop rate: < 0.1%

# 4. Learning
Labeled samples collected: 500+ per week
Model retraining: Completed weekly on schedule
Model improvement: Accuracy up by >0.5% per week

# 5. Scalability
Concurrent MATLAB clients: 10+ without degradation
Throughput: 500+ sensor readings/sec sustained
```

---

## 📞 SUPPORT CONTACTS

| Issue | Contact | Escalation |
|-------|---------|-----------|
| MATLAB integration bugs | Dev Team | Lead Developer |
| API performance | DevOps | Infrastructure |
| Model accuracy drops | ML Engineer | Lead Data Scientist |
| Database issues | DBA | Database Team Lead |
| Emergency outage | On-call | VP Engineering |

---

## 📚 DOCUMENTATION

Start here:
1. **This file** (overview & quick start)
2. `MATLAB_INTEGRATION_PLAN.md` (detailed plan)
3. `matlab_client/MATLAB_INTEGRATION_GUIDE.md` (how to use client)
4. `docs/api/WEBSOCKET_REFERENCE.md` (protocol details)
5. `docs/TROUBLESHOOTING.md` (common problems)

---

## 🎉 NEXT STEPS

1. **Review Plan**: Get team to review this plan
2. **Authorize**: Get approval to start Week 1 tasks
3. **Allocate**: Assign developers to components
4. **Start Week 1**: Begin WebSocket implementation

**Estimated Timeline**: 6 weeks to production  
**Resource Requirement**: 2-3 developers + 1 DevOps  
**Go-Live Date**: Mid-March 2026

---

**Plan Last Updated**: February 12, 2026  
**Status**: Ready for Implementation  
**Confidence Level**: High (proven architecture patterns)
