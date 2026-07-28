# MotorGuard — Digital Twin Predictive Maintenance for Squirrel-Cage Induction Motors

> **UMaT Year 4 Capstone Project** — University of Mines and Technology, Tarkwa, Ghana
> Author: Asare Silas (silasasare246@gmail.com)

A full-stack, real-time predictive maintenance framework that integrates a MATLAB/Simscape physics-based digital twin with a hierarchical multi-modal deep learning AI to monitor, classify, and predict faults in a 75 kW squirrel-cage induction motor driving a centrifugal pump.

---

## Key Results

| Metric | Value |
|---|---|
| F1-macro (5-fold CV) | **0.9089 +/- 0.0134** |
| 95% CI | [0.8971, 0.9206] |
| Accuracy (held-out 300 samples) | **89.33%** |
| Cohen's Kappa | 0.837 |
| ROC-AUC (macro OvR) | 0.9803 |
| RUL MAE (Bi-LSTM standalone) | **1.354 h** |
| RUL R^2 (Bi-LSTM standalone) | **0.9964** |
| Expected Calibration Error | 0.0567 |
| Full pipeline latency (CPU P50) | ~1,050 ms |

---

## System Architecture

```
MATLAB / Simulink / Simscape
  PredictiveMaintenanceClient.m
       WebSocket  ->  ws://localhost:8000/ws/simulink/{id}
       HTTP POST  ->  /api/v1/predict/simulink  (fallback)

FastAPI Backend  (Python 3.11+)
  Model Registry  -- loads 6 .keras + 1 .pkl at startup
  Expert Models
       CWRU-CNN           bearing fault  (4 classes)
       Induction-CNN      motor health   (4 classes)
       Bi-LSTM-Attn       RUL (hours)
       Current-CNN v5     stator / rotor fault (3 classes)
       Thermal-MobileNetV2  thermal state (3 classes)
  XGBoost Meta-Fusion   ->  NORMAL / WARNING / CRITICAL
  Dashboard WebSocket   ->  /ws/dashboard

React Frontend  (Vite + Recharts)
  Live Dashboard  -- health state, RUL gauge, sensor tiles
  Sensor Page     -- real-time signal charts
  Trends Page     -- historical degradation trends
  Diagnostics     -- fault breakdown per expert model
  Report Page     -- downloadable maintenance report
```

---

## Repository Structure

```
backend/                  FastAPI backend
  app/
    api/                  WebSocket handler + REST endpoints
    auth/                 JWT + API-key authentication
    core/                 Config, logging, security
    services/             ModelRegistry, ThermalService, etc.
    main.py               Application entry point
  requirements.txt
  run.py                  Launch server (uvicorn)

frontend/                 React + Vite dashboard
  src/
    components/           TopBar, SensorGrid, ThreePhaseCard ...
    hooks/                useDashboardController
    pages/                Dashboard, Sensors, Trends, Diagnostics, Report
    services/             wsClient, simulationEngine
  package.json

matlab_client/            MATLAB OOP client + Simulink gateway
  PredictiveMaintenanceClient.m
  simulink_predictive_gateway.m
  api_wrapper.m
  motor_params_normal.m
  motor_params_fault.m
  motor_params_critical.m

scripts/                  Training + publication result scripts
  build_latent_digital_twin.py
  generate_meta_features.py
  train_meta_fusion.py
  generate_publication_results.py
  generate_ieee_figures.py   12 IEEE publication figures
  crossval_with_ci.py
  ablation_study_proper.py
  correct_baselines.py
  validate_rul_units.py

src/                      Core Python library
  features/               signal_processing.py, advanced_features.py
  models/                 classifiers, dl_models, rul.py
  data/                   loaders (NASA, CWRU, Induction, Current)
  interface.py            analyze_motor_data() public API

Result_Report/            Research paper metrics and summary
requirements.txt          Root-level Python deps
requirements_exact.txt    Pinned versions (pip freeze output)
```

---

## Quick Start

### Prerequisites

| Tool | Minimum Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| MATLAB | R2020b+ (for Simulink integration) |

### 1. Clone the repository

```bash
git clone https://github.com/asaresilas/MATLAB-Project-Codes.git
cd MATLAB-Project-Codes
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with the following variables:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<your-strong-password>
ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=<your-strong-password>
JWT_SECRET_KEY=<32-char-random-string>
```

Start the backend:

```bash
python run.py
```

The API is now live at `http://127.0.0.1:8000` and interactive docs are at `http://127.0.0.1:8000/docs`.

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at `http://localhost:5173`.

### 4. MATLAB / Simulink integration

```matlab
addpath('matlab_client')
client = PredictiveMaintenanceClient('http://127.0.0.1:8000');
client.connect();
client.predict(sensor_data, sensor_names);
client.close();
```

Parameter files `motor_params_normal.m`, `motor_params_fault.m`, and `motor_params_critical.m` set the three operating regimes. For Simulink, run `simulink_predictive_gateway.m` to configure the gateway block.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/token` | Obtain JWT bearer token |
| POST | `/api/v1/predict/simulink` | Full multi-modal prediction |
| POST | `/api/v1/predict/cwru` | CWRU bearing fault model only |
| POST | `/api/v1/predict/nasa` | NASA Bi-LSTM RUL prediction only |
| POST | `/api/v1/predict/current` | Current-CNN stator/rotor fault only |
| POST | `/api/v1/predict/thermal` | Thermal-MobileNetV2 only |
| WS | `/ws/simulink/{client_id}` | Real-time MATLAB data feed |
| WS | `/ws/dashboard` | Frontend live update stream |

---

## Model Input Specifications

| Model | Input Shape | Output |
|---|---|---|
| CWRU-CNN | (1, 1000, 1) | 4-class softmax (Normal/Inner/Ball/Outer) |
| Induction-CNN | (1, 2048, 1) | 4-class softmax (Healthy/D1/D2/Ring) |
| Bi-LSTM-Attn | (1, 30, 36) | Scalar RUL in hours |
| Current-CNN v5 | (1, 1000, 3) | 3-class softmax (Healthy/Bearing-Fault/BRB) |
| Thermal-MobileNetV2 | Base64 JPEG | 3-class softmax (Normal/Warning/Critical) |
| Meta-Fusion XGBoost | 32-dim feature vector | NORMAL / WARNING / CRITICAL |

The Current-CNN v5 uses a custom `StatisticsExtractor` Keras layer registered under `package="current_feat"`. The model registry handles this automatically on startup.

---

## Fault Conditions Modelled

| Fault | Parameter Changed | Healthy to Fault |
|---|---|---|
| Rotor Imbalance | Unbalanced mass | 5 g to 30 g |
| Shaft Misalignment | Shaft offset | 0 mm to 0.5 mm |
| Bearing Outer-Race Defect | Impact amplitude | 0 to 500 N at BPFO = 200 Hz |
| Thermal Overload | Winding resistance + convection | 0.020 to 0.050 Ohm; hc: 60 to 15 W/m2.K |

### Health-State Thresholds

| State | Latent Degradation (d) | Estimated RUL |
|---|---|---|
| NORMAL | d < 0.33 | > 66 h |
| WARNING | 0.33 <= d < 0.67 | 33 to 66 h |
| CRITICAL | d >= 0.67 | <= 33 h |

Max RUL is 99.41 h based on the NASA IMS bearing dataset end-of-life criterion.

---

## Running Tests

```bash
python -m pytest tests/ -v
python -m pytest tests/test_integration.py::TestDigitalTwinPipeline::test_classifier_training -v
python backend/test_client.py
```

---

## Reproducing Publication Results

Run all scripts from the project root in this order:

```bash
python scripts/build_latent_digital_twin.py
python scripts/generate_meta_features.py
python scripts/train_meta_fusion.py
python scripts/generate_publication_results.py
python scripts/crossval_with_ci.py
python scripts/ablation_study_proper.py
python scripts/correct_baselines.py
python scripts/validate_rul_units.py
python scripts/latency_breakdown_benchmark.py
python scripts/generate_ieee_figures.py
```

**Windows note:** Always use `n_jobs=1` in `StackingClassifier` — `n_jobs=-1` raises a `PermissionError` on restricted Windows environments.

---

## Structural Analysis

The SolidWorks FEA modal analysis of the centrifugal pump and motor assembly (AISI 1035 steel; 28,157 nodes, 13,622 elements) identified five natural frequencies well above the 50 Hz operational excitation, confirming structural safety:

| Mode | Natural Frequency (Hz) |
|---|---|
| 1 | 1,526.02 |
| 2 | 1,531.10 |
| 3 | 1,692.77 |
| 4 | 1,797.90 |
| 5 | 1,884.11 |

---

## License

All benchmark datasets (CWRU Bearing Data Center, NASA IMS) retain their original licences. The project source code is released under the MIT License.

---

## Citation

```
Asare, S. (2026). Development of a Digital Twin Approach for Squirrel-Cage Induction Motor
Predictive Maintenance. UMaT Year 4 Project Report, University of Mines and Technology, Tarkwa.
```

---

## Contact

Silas Asare | silasasare246@gmail.com | https://github.com/asaresilas
