# 🏗️ MATLAB-API INTEGRATION & CONTINUOUS LEARNING PLAN

**Date**: February 12, 2026  
**Objective**: Integrate Predictive Maintenance API with MATLAB/Simulink for real-time learning and inference  
**Scope**: MATLAB client ↔ Python API ↔ TensorFlow Models + Continuous Learning System

---

## 📋 EXECUTIVE SUMMARY

### Vision
Create a robust, fast, and learning-capable bridge between MATLAB/Simulink virtual systems and AI prediction models that:
- ✅ Streams real-time sensor data from virtual systems
- ✅ Provides millisecond-level predictions
- ✅ Continuously learns from incoming data
- ✅ Maintains model accuracy and reliability
- ✅ Handles failures gracefully with fallbacks

### Key Requirements
| Requirement | Target | Acceptance Criteria |
|-------------|--------|-------------------|
| **Communication Speed** | <50ms latency | Prediction response in <50ms |
| **Prediction Accuracy** | >94% | Deep MLP baseline maintained |
| **Data Throughput** | 100-1000 samples/min | Handle continuous streams |
| **Learning Frequency** | Daily/Weekly | Retrain on new data weekly |
| **Server Uptime** | 99.5% | Graceful degradation on failures |
| **Reliability** | Zero data loss | All data logged and recoverable |

---

## 🏛️ ARCHITECTURE OVERVIEW

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATLAB/SIMULINK VIRTUAL SYSTEM               │
│  (Turbofan engines, CNC machines, bearing damage simulation)    │
│                                                                 │
│  ┌── Sensor 1 (Temperature) ───┐                               │
│  ├── Sensor 2 (Vibration) ─────┤                               │
│  ├── Sensor 3 (Current) ───────┤                               │
│  └── Sensor N ─────────────────┘                               │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP/WebSocket (Real-time Stream)
                 │ 10-100 Hz sampling
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON API SERVER (FastAPI)                  │
│                                                                 │
│  ┌─ Ingestion Layer ─────────────────────────────────────┐     │
│  │  • WebSocket endpoint (fast, bidirectional)           │     │
│  │  • Data buffering & validation                        │     │
│  │  • Real-time preprocessing                            │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─ Prediction Layer ────────────────────────────────────┐     │
│  │  • Load 6 AI models (Deep MLP, 1D CNN, TabNet, etc)  │     │
│  │  • Batch inference (1-32 samples)                      │     │
│  │  • Confidence scoring & uncertainty quantification     │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─ Data Persistence Layer ──────────────────────────────┐     │
│  │  • PostgreSQL database (audit trail)                   │     │
│  │  • Time-series DB (InfluxDB for metrics)              │     │
│  │  • File storage (raw data for retraining)             │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─ Retraining Layer ────────────────────────────────────┐     │
│  │  • Weekly batch retraining                            │     │
│  │  • Incremental learning (online learning)             │     │
│  │  • Model versioning & A/B testing                     │     │
│  └───────────────────────────────────────────────────────┘     │
└────────────────┬────────────────────────────────────────────────┘
                 │ Predictions + Confidence
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MATLAB/SIMULINK CLIENT                       │
│  (Displays predictions, controls virtual system)                │
└─────────────────────────────────────────────────────────────────┘

└─ Data Flow:
   Simulink → API (real-time sensor data)
   API → Simulink (predictions, RUL, anomaly scores)
   Simulink + Ground Truth → API (label collection)
   API → Retrain Pipeline (weekly learning)
```

---

## 🔌 COMMUNICATION PROTOCOL STRATEGY

### Option 1: WebSocket (RECOMMENDED FOR REAL-TIME)

**Why WebSocket?**
- ✅ **Persistent connection** - No connection overhead on each message
- ✅ **Bidirectional** - Server can push predictions and data requests
- ✅ **Low latency** - ~1-5ms per message
- ✅ **Efficient** - Less overhead than HTTP polling
- ✅ **Works with MATLAB** - Using websocket communicator

**Architecture**:
```python
# Python API (FastAPI + WebSocket)
@app.websocket("/ws/simulink/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    async for data in websocket.iter_json():
        # Receive: {"timestamp": "2026-02-12T16:00:00", "sensors": [25.3, 0.12, ...]}
        
        # Process
        prediction = model.predict(data["sensors"])
        confidence = get_confidence_score(prediction)
        
        # Send back: {"class": "NORMAL", "confidence": 0.94, "rul_hours": 120}
        await websocket.send_json({
            "timestamp": data["timestamp"],
            "prediction": prediction,
            "confidence": confidence,
            "latency_ms": compute_latency()
        })
```

**MATLAB Integration** (WebSocket):
```matlab
% MATLAB Client
ws = websocket("ws://localhost:8002/ws/simulink/matlab_client_1");

% Send sensor data
sensor_data = struct('timestamp', datetime('now'), 'sensors', [25.3, 0.12, 1.2, ...]);
send(ws, jsonencode(sensor_data));

% Receive prediction
msg = receive(ws);
prediction = jsondecode(msg);
disp(['Predicted Class: ' prediction.class]);
disp(['Confidence: ' num2str(prediction.confidence * 100) '%']);
```

**Performance Targets**:
- ✅ Message latency: 1-5 ms
- ✅ Throughput: 1000 messages/sec per connection
- ✅ Multiple concurrent clients: 10+ simultaneous MATLAB instances

---

### Option 2: REST API with HTTP/2 (ALTERNATIVE)

**When to use**: If WebSocket unavailable or incompatible

```python
@app.post("/api/v1/predict")
async def predict_realtime(sensor_data: SensorInput):
    prediction = model.predict(sensor_data.values)
    return {
        "prediction": prediction,
        "confidence": get_confidence(),
        "latency_ms": elapsed_time
    }
```

**MATLAB Integration** (REST):
```matlab
options = weboptions('MediaType', 'application/json', 'Timeout', 5);
sensor_json = jsonencode(struct('sensors', [25.3, 0.12, ...]));
response = webwrite("http://localhost:8002/api/v1/predict", sensor_json, options);
```

**Comparison**:
| Aspect | WebSocket | REST |
|--------|-----------|------|
| Latency | 1-5 ms | 10-20 ms |
| Overhead | Low | Medium |
| Bidirectional | Yes | Polling needed |
| MATLAB Support | Good | Excellent |
| **Recommendation** | ✅ Primary | Fallback |

---

## ⚡ SERVER RELIABILITY & ROBUSTNESS

### Level 1: Application Layer Reliability

**1.1 Health Monitoring**
```python
# Every request includes health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy" or "degraded" or "offline",
        "models": {
            "deep_mlp": model_loaded and model_accurate,
            "ensemble": model_loaded and model_accurate,
        },
        "database": db_connected,
        "memory_usage_mb": get_memory_usage(),
        "uptime_seconds": get_uptime()
    }
```

**1.2 Error Handling & Fallback Strategies**
```python
async def predict_with_fallback(sensor_data):
    """
    Prediction with cascading fallback:
    1. Try Deep MLP (fastest, 94.1% accuracy)
    2. Fall back to MLP if DMP fails (0.8ms, 91.2%)
    3. Return confidence score indicating fallback
    """
    try:
        # Primary model
        prediction = deep_mlp_model.predict(sensor_data)
        model_used = "Deep MLP"
        confidence = get_confidence_deep_mlp()
    except Exception as e:
        logger.warning(f"Deep MLP failed: {e}")
        try:
            # Backup model
            prediction = mpl_model.predict(sensor_data)
            model_used = "MLP (Backup)"
            confidence = get_confidence_mpl() * 0.95  # Penalize confidence
        except Exception as e2:
            logger.error(f"Both models failed: {e2}")
            prediction = "UNKNOWN"
            confidence = 0.0
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "model_used": model_used,
        "status": "primary" if model_used == "Deep MLP" else "degraded"
    }
```

**1.3 Request Queueing & Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/predict")
@limiter.limit("1000/minute")  # 1000 requests per minute per MATLAB client
async def predict(data: SensorInput):
    # Queued if > 100 concurrent requests
    async with request_queue.get():  # Semaphore limiting
        return await fast_predict(data)
```

**1.4 Data Validation**
```python
class SensorInput(BaseModel):
    sensors: List[float] = Field(..., min_items=14, max_items=14)
    timestamp: datetime
    
    @validator("sensors")
    def validate_ranges(cls, v):
        """Sensor values must be in physical range"""
        for i, val in enumerate(v):
            if val < SENSOR_MIN[i] or val > SENSOR_MAX[i]:
                raise ValueError(f"Sensor {i} out of range: {val}")
        return v
```

---

### Level 2: Database Layer Reliability

**2.1 Persistent Data Storage**
```
PostgreSQL (Main DB)
├── sensor_readings (time-series data)
│   ├── timestamp (indexed)
│   ├── simulink_session_id
│   ├── sensor_values (float array)
│   ├── ground_truth (NULL until available)
│   └── data_quality (0-1 score)
│
├── predictions (audit trail)
│   ├── timestamp
│   ├── sensor_reading_id (FK)
│   ├── prediction_class
│   ├── confidence
│   ├── model_version
│   ├── latency_ms
│   └── was_correct (NULL → TRUE/FALSE after ground truth)
│
├── model_versions (version control)
│   ├── version_id (e.g., "deep_mlp_v1.2")
│   ├── training_date
│   ├── training_samples
│   ├── accuracy_on_testset
│   ├── accuracy_on_production (continuously updated)
│   ├── status (active/archived)
│   └── file_path (model storage)
│
└── model_retrainings (learning history)
    ├── retraining_id
    ├── start_timestamp
    ├── end_timestamp
    ├── samples_used
    ├── model_version_before
    ├── model_version_after
    ├── accuracy_improvement
    └── status (success/failed)
```

**2.2 Automatic Backup & Recovery**
```bash
# Daily backup at 2 AM
0 2 * * * pg_dump prod_db | gzip > /backups/prod_db_$(date +\%Y\%m\%d).sql.gz

# Weekly full backup to cloud
0 3 * * 0 aws s3 sync /backups s3://company-backups/ml-system/ --delete

# Replication to standby server
# PostgreSQL streaming replication to backup instance (automatic failover)
```

**2.3 Connection Pooling**
```python
from sqlalchemy.pool import QueuePool

database_url = "postgresql://user:pass@localhost/ml_system"
engine = create_async_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,  # 20 concurrent connections
    max_overflow=10,  # Up to 30 total
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600  # Recycle connections hourly
)
```

---

### Level 3: Infrastructure Layer Reliability

**3.1 Process Monitoring & Auto-Restart**
```
systemd service (Linux) / NSSM (Windows)

[Service]
Type=simple
User=ml_user
ExecStart=/usr/bin/python -m uvicorn backend.app.main:app
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal
```

**3.2 Load Balancing (for scale)**
```
                    ┌─────────────────────┐
                    │   Nginx Reverse     │
                    │   Load Balancer     │
                    │  (Port 8000)        │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ↓             ↓             ↓
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ API Server 1 │ │ API Server 2 │ │ API Server 3 │
        │ (8002)       │ │ (8003)       │ │ (8004)       │
        └──────────────┘ └──────────────┘ └──────────────┘
                 │             │             │
                 └─────────────┼─────────────┘
                               ↓
                    ┌─────────────────────┐
                    │  PostgreSQL DB      │
                    │  (Shared state)     │
                    └─────────────────────┘
```

**3.3 Monitoring & Alerting**
```
Prometheus (metrics collection)
  └─ Metrics: requests/sec, latency, error rate, model accuracy
  
Grafana (visualization)
  └─ Dashboards: Real-time performance, model drift detection
  
AlertManager (alerting)
  ├─ Alert: Latency > 100ms
  ├─ Alert: Error rate > 1%
  ├─ Alert: Model accuracy drop > 2%
  ├─ Alert: Retraining failure
  └─ Alert: Database connection lost
```

---

## 📊 CONTINUOUS LEARNING STRATEGY

### Phase 1: Data Collection (Real-time)

**1.1 Streaming Data Pipeline**
```
MATLAB Simulink
    ↓ (WebSocket, 10-100 Hz)
Real-time Buffer (in-memory, 10-minute sliding window)
    ↓ (Every 100 samples OR every 10 minutes)
PostgreSQL sensor_readings table
    ↓
Backup storage (/data/raw_data/YYYYMMDD/)
```

**1.2 Handling Ground Truth**
```matlab
% In MATLAB: When virtual system reaches known state (failure/normal)
% Send ground truth label back to API

websocket_send({
    'timestamp': prediction_timestamp,
    'ground_truth': 'bearing_failure_outer_race',
    'actual_time_to_failure_hours': 45,
    'confidence_in_label': 0.99
});

% This updates PostgreSQL predictions.was_correct = TRUE/FALSE
```

---

### Phase 2: Weekly Retraining

**Trigger**: Every Monday 2 AM (low-traffic time)

**2.1 Retraining Pipeline**
```
Step 1: Aggregate Data (Automated)
├─ Query: SELECT * FROM sensor_readings WHERE created_at > 7 days ago
├─ Filter: Only rows where ground_truth IS NOT NULL
├─ Count: Expected ~500-2000 new labeled samples per week
└─ Status: Data collected from Simulink + any manual labeling

Step 2: Data Preparation
├─ Normalize: Apply StandardScaler (same as training)
├─ Validation: Remove outliers (>5σ)
├─ Splitting: 70% train, 15% val, 15% test
└─ Balance: Handle class imbalance (if any)

Step 3: Model Retraining
├─ Load: best_model_Deep_MLP v1.2 (current production)
├─ Train: Fine-tune on new data for 10 epochs
├─ Validate: Check accuracy on validation set
│  └─ If accuracy ≥ current accuracy - 1%: PASS
│  └─ If accuracy < current accuracy - 1%: FAIL (abort)
├─ Test: Evaluate on held-out test set
│  └─ Report metrics: Accuracy, Precision, Recall, F1
└─ Version: Save as best_model_Deep_MLP v1.3

Step 4: A/B Testing (2-4 weeks)
├─ Deploy: New model (v1.3) handles 10% of MATLAB requests
├─ Monitor: Compare v1.2 vs v1.3 accuracy on live data
├─ Decision: If v1.3 better after 2 weeks → Make it primary
│  └─ Yes: Promote to 100%, v1.2 becomes backup
│  └─ No: Rollback to v1.2, investigate why v1.3 failed

Step 5: Logging & Reporting
├─ Record: model_retrainings table entry
├─ Send Slack notification: "Retraining complete. New accuracy: 94.3%"
└─ Archive: Training logs and model artifacts
```

**2.2 Continuous Incremental Learning (Optional Advanced)**
```python
# Instead of weekly batch, update model incrementally
class OnlineLearningUpdater:
    def __init__(self, model, update_frequency=100):
        self.model = model
        self.update_frequency = update_frequency  # Every 100 new labeled samples
        self.labeled_samples = []
    
    async def add_labeled_sample(self, sensor_data, ground_truth):
        """Called when ground truth becomes available"""
        self.labeled_samples.append((sensor_data, ground_truth))
        
        if len(self.labeled_samples) >= self.update_frequency:
            await self.incremental_update()
    
    async def incremental_update(self):
        """Lightweight update (not full retraining)"""
        X = np.array([s[0] for s in self.labeled_samples])
        y = np.array([s[1] for s in self.labeled_samples])
        
        # Fit-transform scaler on new data only
        X_scaled = self.scaler.partial_fit(X).transform(X)
        
        # Fine-tune model on new data (1-2 epochs only)
        self.model.fit(X_scaled, y, epochs=2, verbose=0)
        
        # Validate on held-out test set
        test_accuracy = self.validate()
        
        if test_accuracy >= self.last_accuracy - 0.01:
            logger.info(f"Incremental update successful. Acc: {test_accuracy:.1%}")
            self.last_accuracy = test_accuracy
            self.labeled_samples = []
        else:
            logger.warning(f"Incremental update rejected. Acc dropped.")
            self.reload_last_good_model()
```

---

### Phase 3: Model Drift Detection

**3.1 Performance Monitoring**
```python
class ModelDriftDetector:
    def __init__(self, baseline_accuracy=0.941, window_size=1000):
        self.baseline_accuracy = baseline_accuracy
        self.window_size = window_size
        self.recent_predictions = []
    
    async def check_drift(self):
        """Run every hour"""
        if len(self.recent_predictions) < self.window_size:
            return  # Not enough data yet
        
        # Calculate recent accuracy on known labels
        recent_correct = sum([p['was_correct'] for p in self.recent_predictions])
        recent_accuracy = recent_correct / len(self.recent_predictions)
        
        accuracy_drop = self.baseline_accuracy - recent_accuracy
        
        if accuracy_drop > 0.03:  # Accuracy dropped >3%
            logger.error(f"DRIFT DETECTED: Accuracy dropped to {recent_accuracy:.1%}")
            await self.trigger_alert("Model accuracy dropped significantly")
            await self.queue_emergency_retraining()
        elif accuracy_drop > 0.01:  # Accuracy dropped >1%
            logger.warning(f"Minor drift: Accuracy at {recent_accuracy:.1%}")
```

**3.2 Concept Drift Handling**
```
If virtual systems change (e.g., new bearing type):
  → Ground truth labels will show different patterns
  → Model drift detector identifies this automatically
  → Emergency retraining triggered
  → New model version trained on new concept
  → A/B test new model
  → Gradual rollout to avoid disruption
```

---

## 🚀 COMMUNICATION PROTOCOL IMPLEMENTATION

### 1. WebSocket Server Implementation

```python
# File: backend/app/websocket_handler.py

from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
from collections import deque

class SimulinkConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.client_buffers: dict[str, deque] = {}
        self.connection_stats: dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_buffers[client_id] = deque(maxlen=1000)
        self.connection_stats[client_id] = {
            "connected_at": datetime.now(),
            "messages_received": 0,
            "messages_sent": 0,
            "total_latency_ms": 0,
            "avg_latency_ms": 0,
        }
        logger.info(f"MATLAB Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            stats = self.connection_stats[client_id]
            logger.info(
                f"MATLAB Client disconnected: {client_id}. "
                f"Total messages: {stats['messages_received']}, "
                f"Avg latency: {stats['avg_latency_ms']:.2f}ms"
            )
    
    async def broadcast(self, client_id: str, message: dict):
        """Send message to MATLAB client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                self.connection_stats[client_id]["messages_sent"] += 1
            except Exception as e:
                logger.error(f"Failed to send to {client_id}: {e}")
                self.disconnect(client_id)

manager = SimulinkConnectionManager()

@app.websocket("/ws/simulink/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive sensor data from MATLAB/Simulink
            data = await websocket.receive_json()
            
            # Timestamp the incoming data
            receive_time = time.time()
            
            try:
                # Extract sensor values
                sensors = np.array(data.get("sensors", []))
                timestamp = data.get("timestamp", datetime.now().isoformat())
                
                # Validate data
                if len(sensors) != 14:  # Expected sensor count
                    raise ValueError(f"Expected 14 sensors, got {len(sensors)}")
                
                # Store in buffer (for retraining)
                manager.client_buffers[client_id].append({
                    "timestamp": timestamp,
                    "sensors": sensors.tolist(),
                    "client_id": client_id
                })
                
                # Make prediction (fast path)
                prediction = await fast_predict(sensors)
                
                # Calculate latency
                latency_ms = (time.time() - receive_time) * 1000
                
                # Prepare response
                response = {
                    "timestamp": timestamp,
                    "prediction": {
                        "class": prediction["class"],
                        "confidence": float(prediction["confidence"]),
                        "model_version": "deep_mlp_v1.2"
                    },
                    "performance": {
                        "latency_ms": latency_ms,
                        "inference_time_ms": prediction.get("inference_time_ms")
                    },
                    "server": {
                        "health": "healthy",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # Send prediction back to MATLAB
                await manager.broadcast(client_id, response)
                
                # Update stats
                stats = manager.connection_stats[client_id]
                stats["messages_received"] += 1
                stats["total_latency_ms"] += latency_ms
                stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["messages_received"]
                
            except Exception as e:
                logger.error(f"Error processing data from {client_id}: {e}")
                await manager.broadcast(client_id, {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

---

### 2. MATLAB Client Implementation

```matlab
% File: matlab_client/PredictiveMaintenanceClient.m

classdef PredictiveMaintenanceClient
    properties (Access = private)
        ws              % WebSocket object
        server_url
        client_id
        is_connected
        prediction_history   % Buffer of recent predictions
        latency_history      % Buffer of recent latencies
    end
    
    methods
        function obj = PredictiveMaintenanceClient(server_url, client_id)
            % Constructor
            obj.server_url = server_url;
            obj.client_id = client_id;
            obj.is_connected = false;
            obj.prediction_history = [];
            obj.latency_history = [];
        end
        
        function connect(obj)
            % Establish WebSocket connection to API server
            try
                ws_url = sprintf("%s/ws/simulink/%s", ...
                    strrep(obj.server_url, 'http', 'ws'), obj.client_id);
                obj.ws = websocket(ws_url);
                obj.is_connected = true;
                fprintf('[Connected] Predictive Maintenance Client\n');
            catch ME
                fprintf('[ERROR] Connection failed: %s\n', ME.message);
                obj.is_connected = false;
            end
        end
        
        function prediction = predict(obj, sensor_values)
            % Send sensor data and receive prediction
            % 
            % Input:
            %   sensor_values: [1x14] or [14x1] array of sensor readings
            %
            % Output:
            %   prediction: struct with fields:
            %     - class: predicted fault class (string)
            %     - confidence: confidence score (0-1)
            %     - latency_ms: round-trip latency
            
            if ~obj.is_connected
                error('Not connected to API server');
            end
            
            % Validate input
            sensor_values = sensor_values(:);  % Ensure column vector
            if length(sensor_values) ~= 14
                error('Expected 14 sensor values');
            end
            
            % Prepare message
            message = struct( ...
                'timestamp', datetime.now().isoformat(), ...
                'sensors', num2cell(sensor_values));
            
            % Send to API
            send(obj.ws, jsonencode(message));
            
            % Wait for response (with timeout)
            timeout_sec = 5;
            response_msg = receive(obj.ws, timeout_sec);
            
            % Parse response
            try
                response = jsondecode(response_msg);
                prediction = struct( ...
                    'class', response.prediction.class, ...
                    'confidence', response.prediction.confidence, ...
                    'latency_ms', response.performance.latency_ms, ...
                    'model_version', response.prediction.model_version);
            catch ME
                error('Invalid response from server: %s', ME.message);
            end
        end
        
        function send_ground_truth(obj, timestamp, ground_truth_label, actual_rul)
            % Send ground truth label (when failure actually occurs)
            %
            % Input:
            %   timestamp: ISO timestamp of when we made the prediction
            %   ground_truth_label: string describing actual failure
            %   actual_rul: actual time to failure in hours
            
            message = struct( ...
                'type', 'ground_truth', ...
                'prediction_timestamp', timestamp, ...
                'ground_truth', ground_truth_label, ...
                'actual_rul_hours', actual_rul, ...
                'confidence_in_label', 0.99);
            
            try
                send(obj.ws, jsonencode(message));
                fprintf('[Ground Truth Sent] %s: %s\n', timestamp, ground_truth_label);
            catch ME
                fprintf('[WARNING] Failed to send ground truth: %s\n', ME.message);
            end
        end
        
        function disconnect(obj)
            % Disconnect from server
            if obj.is_connected
                close(obj.ws);
                obj.is_connected = false;
                fprintf('[Disconnected] Predictive Maintenance Client\n');
            end
        end
        
        function avg_latency = get_average_latency(obj)
            % Get average latency of recent predictions
            if isempty(obj.latency_history)
                avg_latency = NaN;
            else
                avg_latency = mean(obj.latency_history);
            end
        end
        
        function delete(obj)
            % Destructor - always disconnect on cleanup
            obj.disconnect();
        end
    end
end


% Example Usage in Simulink
% ======================

% In Simulink Initialization (on model load):
clear all;
global pm_client;
pm_client = PredictiveMaintenanceClient(...
    'http://localhost:8002', ...
    'simulink_instance_1');
pm_client.connect();

% In Simulink Step Function (every simulation timestep):
function predict_step(block)
    global pm_client;
    
    % Get sensor readings from Simulink simulation
    sensor_values = block.InputPort(1).Data;  % [T, V, I, ...] from model
    
    try
        % Get prediction from API
        result = pm_client.predict(sensor_values);
        
        % Send outputs to Simulink
        block.OutputPort(1).Data = categorical(result.class);
        block.OutputPort(2).Data = result.confidence;
        block.OutputPort(3).Data = result.latency_ms;
        
        % Log for analysis
        fprintf('[%s] Class: %s | Confidence: %.1f%% | Latency: %.1f ms\n', ...
            datetime.now().isoformat(), result.class, result.confidence*100, result.latency_ms);
        
    catch ME
        fprintf('[ERROR] Prediction failed: %s\n', ME.message);
        block.OutputPort(1).Data = categorical('ERROR');
        block.OutputPort(2).Data = 0;
        block.OutputPort(3).Data = -1;
    end
end

% In Simulink (when failure occurs - Matlab script or triggered subsystem):
function log_actual_failure()
    global pm_client pm_prediction_timestamp;
    
    actual_failure_type = 'bearing_outer_race_fault';
    actual_time_to_failure = 45;  % hours
    
    pm_client.send_ground_truth( ...
        pm_prediction_timestamp, ...
        actual_failure_type, ...
        actual_time_to_failure);
end
```

---

## 🔍 TESTING & VALIDATION STRATEGY

### Phase 1: Unit Testing

```python
# File: tests/test_websocket_communication.py

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test: MATLAB client can connect to WebSocket"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with pytest.raises(Exception):  # Expected: upgrade needed
            # WebSocket testing requires special setup
            pass

@pytest.mark.asyncio
async def test_prediction_latency():
    """Test: Predictions complete within 50ms"""
    import time
    
    sensor_data = np.random.randn(14)
    
    start = time.time()
    prediction = await fast_predict(sensor_data)
    elapsed = (time.time() - start) * 1000
    
    assert elapsed < 50, f"Latency {elapsed}ms exceeds 50ms threshold"

@pytest.mark.asyncio
async def test_error_handling():
    """Test: Invalid sensor data handled gracefully"""
    bad_data = [1.0, 2.0]  # Only 2 sensors, needs 14
    
    with pytest.raises(ValueError):
        await fast_predict(bad_data)

def test_fallback_model():
    """Test: Backup model works if primary fails"""
    # Temporarily disable Deep MLP
    models['deep_mlp'] = None
    
    prediction = predict(good_sensor_data)
    assert prediction['model_used'] == 'MLP (Backup)'
    assert prediction['confidence'] < 0.9  # Penalized confidence
    
    # Re-enable
    models['deep_mlp'] = load_model('best_model_Deep_MLP.keras')
```

### Phase 2: Integration Testing

```python
# File: tests/test_matlab_integration.py

@pytest.mark.asyncio
async def test_matlab_websocket():
    """Test: Simulate MATLAB client connecting and sending data"""
    
    # Create test WebSocket connection
    async with AsyncClient(app=app) as client:
        async with client.websocket_connect("/ws/simulink/test_client") as ws:
            # Send sensor data
            msg = {"sensors": [25.3, 0.12, 1.2, ...], "timestamp": "2026-02-12T16:00:00"}
            await ws.send_json(msg)
            
            # Receive prediction
            response = await ws.receive_json()
            
            assert "prediction" in response
            assert "confidence" in response["prediction"]
            assert response["performance"]["latency_ms"] < 50

@pytest.mark.asyncio
async def test_continuous_data_stream():
    """Test: 100 consecutive predictions maintain accuracy"""
    
    predictions = []
    latencies = []
    
    async with client.websocket_connect("/ws/simulink/stream_test") as ws:
        for i in range(100):
            sensor_data = generate_realistic_sensor_data()
            await ws.send_json({"sensors": sensor_data, "timestamp": ...})
            response = await ws.receive_json()
            predictions.append(response["prediction"]['class'])
            latencies.append(response["performance"]["latency_ms"])
    
    # Verify
    assert all(l < 50 for l in latencies), f"Some predictions latent: {[l for l in latencies if l >= 50]}"
    assert accuracy_score(predictions, expected) > 0.90
```

### Phase 3: Load Testing

```bash
# File: tests/load_test.sh

#!/bin/bash

echo "Starting API Server..."
python servers/run_server.py &
API_PID=$!
sleep 45

echo "Running load test: 100 concurrent MATLAB clients, 1000 requests each"

for i in {1..100}; do
    (
        for j in {1..1000}; do
            curl -N \
              -H "Content-Type: application/json" \
              -d '{"sensors": [25.3, 0.12, ...]}' \
              http://localhost:8002/api/v1/predict \
              >> test_results/load_test_client_$i.txt
        done
    ) &
done

wait

echo "Load test complete. Analyzing results..."
# Analyze latencies, success rates, etc.

kill $API_PID
```

### Phase 4: End-to-End Testing with Simulink

```matlab
% File: tests/test_matlab_to_api.m

% Start API server
system('cd .. && python servers/run_server.py &');
pause(60);  % Wait for models to load

% Create MATLAB client
pm_client = PredictiveMaintenanceClient('http://localhost:8002', 'test_client');
pm_client.connect();

% Run tests
num_tests = 100;
latencies = [];
accuracies = [];

for i = 1:num_tests
    % Generate realistic sensor data
    sensor_data = randn(14, 1) .* sensor_std + sensor_mean;
    
    % Get prediction
    tic;
    prediction = pm_client.predict(sensor_data);
    latencies(i) = prediction.latency_ms;
    accuracies(i) = contains(categories(prediction.class), 'NORMAL');
end

% Verify performance
avg_latency = mean(latencies);
p95_latency = prctile(latencies, 95);
avg_accuracy = mean(accuracies);

fprintf('Results:\n');
fprintf('  Average Latency: %.2f ms\n', avg_latency);
fprintf('  95th Percentile Latency: %.2f ms\n', p95_latency);
fprintf('  Average Accuracy: %.2f%%\n', avg_accuracy * 100);

assert(avg_latency < 50, 'Average latency exceeds 50ms');
assert(p95_latency < 100, '95th percentile latency exceeds 100ms');
assert(avg_accuracy > 0.90, 'Accuracy below 90%');

fprintf('\n✅ All tests passed!\n');

pm_client.disconnect();
```

---

## 📈 PERFORMANCE TARGETS & MONITORING

### Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Prediction Latency (P50)** | <20 ms | Time from sensor receipt to response send |
| **Prediction Latency (P95)** | <50 ms | 95th percentile latency |
| **Prediction Accuracy** | >94% | On validation set from labeled MATLAB data |
| **Model Uptime** | 99.5% | Excluding planned maintenance |
| **Error Rate** | <1% | Failed predictions / total predictions |
| **Throughput** | 1000 msg/sec | Per server instance |
| **Data Loss** | 0% | All sensor data persisted |
| **Retraining Success** | 100% | All weekly retrainings complete |
| **MATLAB Connection** | <5 min reconnect | If connection drops |

### Monitoring Dashboard (Grafana)

```
Real-Time Panel:
├─ Current latency (line chart, 1-hour window)
├─ Prediction distribution (pie chart: Normal, Fault 1, Fault 2, ...)
├─ Model accuracy (gauge: >94% = green, <91% = red)
├─ Active MATLAB clients (number)
├─ Data throughput (msg/sec)
└─ Server health (status indicator)

Training Panel:
├─ Last retraining date
├─ New model accuracy vs previous
├─ Samples collected since last training
├─ Scheduled next training date
└─ A/B test status (% traffic to new model)

Database Panel:
├─ Total sensor records stored
├─ Database size (GB)
├─ Backup status
└─ Query latency
```

---

## 🛠️ IMPLEMENTATION ROADMAP

### Week 1: Foundation
- [ ] Set up WebSocket endpoint in FastAPI
- [ ] Implement MATLAB client class
- [ ] Test basic connectivity
- [ ] Set up PostgreSQL database
- [ ] Create data persistence layer

### Week 2: Prediction System
- [ ] Implement fast prediction path
- [ ] Add error handling & fallback models
- [ ] Set up request queuing
- [ ] Implement latency tracking
- [ ] Create health check endpoints

### Week 3: Data Collection & Learning
- [ ] Implement data collection pipeline
- [ ] Create retraining scheduler
- [ ] Set up Model versioning system
- [ ] Implement A/B testing framework
- [ ] Create ground truth collection mechanism

### Week 4: Reliability & Monitoring
- [ ] Set up database replication
- [ ] Implement auto-backup system
- [ ] Deploy monitoring (Prometheus + Grafana)
- [ ] Set up alerting
- [ ] Create runbook for common issues

### Week 5: Testing & Validation
- [ ] Unit tests for all components
- [ ] Integration tests with MATLAB
- [ ] Load testing (100 concurrent clients)
- [ ] Stress testing (1000 concurrent clients)
- [ ] Failure recovery testing

### Week 6: Deployment & Documentation
- [ ] Deploy to production server
- [ ] Create MATLAB integration guide
- [ ] Write system documentation
- [ ] Train support team
- [ ] Go-live with monitoring

---

## 🔐 SECURITY CONSIDERATIONS

```python
# Authentication: OAuth2 with bearer tokens
@app.post("/api/v1/token")
async def login(username: str, password: str):
    """MATLAB clients must authenticate"""
    user = verify_credentials(username, password)
    token = create_jwt_token(user, expires_hours=24)
    return {"access_token": token}

# MATLAB uses token:
# ws_url = f"wss://localhost:8002/ws/simulink/matlab_client_1?token={token}"

# Rate limiting
@limiter.limit("100/minute")
async def predict():
    """Prevent MATLAB from overwhelming server"""

# Encryption: TLS/SSL for all connections
# wss:// (WebSocket Secure) instead of ws://
```

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Slow Predictions** | Latency >100ms | Check if backup model active, restart server |
| **MATLAB Connection Timeout** | WebSocket disconnect every 5 min | Increase timeout, check firewall |
| **Model Accuracy Drops** | Accuracy <90% | Check data quality, trigger emergency retraining |
| **Database Full** | Disk space errors | Archive old data, increase storage |
| **Retraining Fails** | Model not updating | Check training data quality, validate labels |

---

## ✅ SUCCESS CRITERIA

Project is successful if:
- ✅ MATLAB sends 100 sensor samples/sec for 1 hour continuously
- ✅ API responds to each in <50ms (P95 latency)
- ✅ Predictions remain >94% accurate
- ✅ Server uptime >99.5% for 1 month
- ✅ Weekly retraining completes automatically
- ✅ Model improvement detected after 2-3 weeks of data collection
- ✅ MATLAB can receive and process predictions in real-time
- ✅ Zero data loss (all sensor data persisted)
- ✅ Automated drift detection triggers correctly

---

**Plan Prepared**: February 12, 2026  
**Status**: Ready for implementation  
**Next Step**: Review with team and begin Week 1 tasks

