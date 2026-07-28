# MotorGuard Predictive Maintenance Digital Twin — Project Summary

**Project:** UMaT Year 4 Capstone — Predictive Maintenance Digital Twin for Electric Motors  
**Institution:** University of Mines and Technology (UMaT), Tarkwa, Ghana  
**Department:** Electrical and Electronic Engineering  
**Year:** 2025–2026  

---

## 1. Project Overview

MotorGuard is a full-stack real-time predictive maintenance system for a 75 kW, 400 V, 50 Hz, 4-pole IEC 280M squirrel-cage induction motor (SCIM). It integrates a physics-based MATLAB/Simulink digital twin with five deep learning expert models and a hierarchical meta-fusion classifier to diagnose motor faults, predict remaining useful life (RUL), and deliver results to a live React dashboard via a WebSocket-connected FastAPI backend.

The system addresses the central challenge of multi-modal predictive maintenance: each sensing modality (vibration, current, temperature, thermal imaging) provides complementary fault information, but no single modality captures the full picture. The hierarchical meta-fusion approach aggregates all five expert opinions into a single health classification (NORMAL / WARNING / CRITICAL) with calibrated confidence.

---

## 2. System Architecture

```
MATLAB/Simulink Digital Twin
  └─ motor_params_*.m           → Operating condition parameters (Normal/Fault/Critical)
  └─ simulink_predictive_gateway.m → Ring-buffer accumulation + vibration synthesis
  └─ api_wrapper.m              → WebSocket connection to FastAPI backend
  └─ PredictiveMaintenanceClient.m → MATLAB OOP WebSocket client

FastAPI Backend (backend/)
  └─ WebSocket handler          → Routes payloads → PredictionEngine
  └─ PredictionEngine           → Runs 5 expert models + physics gate + meta-fusion
  └─ ModelRegistry              → Loads all .keras models at startup
  └─ thermal_service.py         → Handles thermal matrix → MobileNetV2

React Frontend (frontend/)
  └─ Dashboard                  → Live health overview
  └─ Live Sensors               → Gauges, charts, 3-phase current
  └─ Diagnostics                → AI predictions, fault type, RUL, expert confidence
  └─ Reports                    → Printable IEC/ISO maintenance report
  └─ Trends                     → Time-series trend analysis
```

---

## 3. Models Used

### Expert Models (Trained on Real Benchmark Datasets)

| Model | Dataset | Architecture | Input | Output |
|-------|---------|--------------|-------|--------|
| CWRU-CNN | CWRU Bearing (12 kHz) | 1D CNN | (1000, 1) | 4-class bearing fault |
| Induction-CNN | Treml Induction HDF5 | 1D CNN | (2048, 1) | 4-class motor health |
| NASA Bi-LSTM-Attn | NASA IMS run-to-failure | Bi-LSTM + Attention | (30, 36) | RUL (hours) |
| Current-CNN v5 | Mendeley Current Signature | StatisticsExtractor MLP | (1000, 3) | 3-class current fault |
| Thermal-MobileNetV2 | Real IR images (369 samples) | Transfer learning | base64 JPEG | 3-class thermal fault |

### Meta-Fusion Classifier

- **Architecture:** XGBoost StackingClassifier
- **Input:** 32-dimensional meta-feature vector (expert probabilities + Shannon entropy + decision margin + inter-expert variance + scalar safety features)
- **Output:** NORMAL / WARNING / CRITICAL health classification
- **Validated F1-macro (5-fold CV):** 0.9089 ± 0.0134 [95% CI: 0.8971, 0.9206]

---

## 4. Key Design Decisions and Assumptions

### Vibration Signal Synthesis
Simscape Multibody rigid-joint constraints absorb bearing reaction forces internally, producing near-zero constraint residuals (~1e-13 m/s²). The gateway synthesises the bearing housing acceleration from three independent physics-based sources:

**1. Bearing outer-race defect (BPFO impact train)**  
Each outer-race defect strike produces an exponentially decaying impulse at the bearing resonance frequency (~2500 Hz) at a repetition rate equal to BPFO (≈88.1 Hz at 1480 RPM). Amplitude scales with `A_impact` (N):
```
a_defect = (A_impact / 300) × exp(−400 × t_phase) × sin(2π × 2500 × t_phase)
```
Parameters: 0 N (Normal), 120 N (Fault), 350 N (Critical)

**2. Shaft misalignment (2× synchronous, ISO 13373-3)**  
Shaft-coupling radial offset generates a 2× running-speed restoring force via Hooke's law:
```
A_misalign = (k_coupling × delta_offset) / m_housing = (1×10⁵ × δ) / 145
```
Parameters: δ = 0 mm (Normal), 0.3 mm (Fault), 1.5 mm (Critical)

**3. Rotor imbalance (1× synchronous, ISO 1940-1)**  
Residual unbalance produces a centrifugal force rotating with the shaft:
```
A_imbalance = (U_rotor × ω²) / m_rotor = (U_rotor × ω²) / 45
```
U_rotor values: 200 g·mm (Normal — ISO G2.5 grade), 800 g·mm (Fault — 4× healthy), 2500 g·mm (Critical — exceeds G6.3 alarm limit)

**Synthesis rate:** 12 000 Hz to match CWRU training dataset. All signals in m/s²; converted to g by api_wrapper before transmission.

### Physics Gate (Domain Shift Correction)
CNN models trained on real test-rig data tend to predict faults on synthetic Simulink sinusoids even when all physical parameters indicate a healthy motor. A physics gate forces NORMAL when all four conditions hold simultaneously:
- Vibration RMS < 1.5 g (ISO 10816-3 Zone A/B boundary)
- Stator temperature < 85 °C (well below IEC 60034-1 Class F warning at 95 °C)
- Temperature rise ΔT < 40 K (below IEC 60034-1 Class F rise warning at 50 K)
- Phase current RMS < 129 A (below rated 132 A line current)

### Fault Code — Categorical Not Bitmask
The backend outputs a categorical fault_code (0=Healthy, 1=Bearing, 2=Rotor, 3=Shaft, 4=Thermal, 5=Multiple Faults) rather than a bitmask. The MATLAB gateway reads this single integer and the Simulink Fault_Type port displays a clean code.

### Accuracy Reporting
The Simulink Accuracy output is fixed at 90.89 % (validated F1-macro from 5-fold cross-validation). The old formula `(1 − uncertainty) × 100` always returned 100 % because the backend uses a single deterministic forward pass (n_iter=1), making uncertainty=0 always.

### Temperature Units
All temperatures throughout the system are in °C. The backend's `_to_celsius()` function handles both Kelvin (>100) and Celsius inputs automatically. The frontend displays °C. The MATLAB workspace receives temperatures in Kelvin from Simscape and the gateway passes them directly — the backend handles the conversion.

### IEC 60034-1 Class F Thresholds
- Stator winding: Warning 95 °C, Critical 120 °C (absolute temperature)
- Temperature rise ΔT: Warning 50 K, Critical 70 K
- These are Class F absolute limits, not the temperature RISE limits (which are 105 K above 40 °C ambient = 145 °C absolute max — the rise limit is for sizing, not for real-time alarms)

### RUL Units
All RUL values are in **hours**, not percentage. The NASA Bi-LSTM-Attn model was trained on NASA IMS run-to-failure data where the target is time-to-failure in hours. MAE = 23.011 h, RMSE = 26.810 h.

---

## 5. Experimental Conditions

Three Simulink simulation scenarios corresponding to the three motor operating states:

| Parameter | NORMAL | WARNING | CRITICAL | Standard / Rationale |
|-----------|--------|---------|----------|----------------------|
| Script | `motor_params_normal.m` | `motor_params_fault.m` | `motor_params_critical.m` | — |
| Bearing impact (A_impact) | 0 N | 120 N | 350 N | CWRU severity 0 / 1 / 3 |
| Shaft offset (δ) | 0 mm | 0.3 mm | 1.5 mm | ISO 13373-3 mild/severe |
| Rotor unbalance (U_rotor) | 200 g·mm | 800 g·mm | 2500 g·mm | ISO 1940-1 G2.5 / 4× / alarm |
| Expected vib. RMS | ~0.04 g | ~1.0–1.5 g | ~3.5–4.5 g | ISO 10816-3 Zone A / B / D |
| Stator temp. | 60 °C | 95 °C | 130 °C | IEC 60034-1 Class F |
| Phase current (Ia) | 85 A | 110 A | 138 A | 65% / 83% / 105% rated |
| Rotor speed | 1480 RPM | 1465 RPM | 1440 RPM | 1% / 2.3% slip from nom. |

Motor: 75 kW, 400 V, 50 Hz, 4-pole, IEC 280M SCIM  
Bearing: SKF 6316 deep-groove (n=9 balls, d=25.4 mm, D_pitch=120.65 mm), BPFO ≈ 88.1 Hz at 1480 RPM  
Rotor mass: 45 kg (IEC 280M frame reference)  
Housing mass: 145 kg (used in misalignment force→acceleration conversion)  
Vibration synthesis: 12 000 Hz, 2048-sample ring buffer → prediction every ~170 ms  

---

## 6. Software Stack

| Layer | Technology |
|-------|-----------|
| Simulation | MATLAB R2023b / Simulink / Simscape Multibody |
| Backend | Python 3.10, FastAPI 0.103, uvicorn, TensorFlow 2.13 |
| ML | scikit-learn 1.3, XGBoost 3.0, joblib |
| Frontend | React 18, Vite 5, CSS custom properties (no UI framework) |
| Communication | WebSocket (ws://127.0.0.1:8000/ws/simulink/{id}) + HTTP fallback |
| Hardware | AMD64 Family 23, 4-core/8-thread, 23.5 GB RAM, CPU-only |

---

## 7. Results Summary

- **Meta-fusion F1-macro (5-fold CV):** 0.9089 ± 0.0134
- **CWRU-CNN real-data accuracy:** 100 % (bearing fault classification)
- **NASA Bi-LSTM RUL MAE:** 1.354 hours, R² = 0.9964
- **Current-CNN v5 holdout accuracy:** 87.93 %
- **Full pipeline P50 latency:** ~1050 ms (CPU-only, single sample)
- **Calibration ECE:** 0.0567 (well-calibrated, deterministic Shannon entropy)
- **McNemar's test:** Statistically significant improvement over all baselines (p < 0.0001)

---

## 8. Known Limitations

1. **Induction-CNN temporal shift:** 53.33 % accuracy due to chronological train/test split revealing distribution shift. The model has 4 output classes but the test cache has 3 classes (Fault-D2 → 0 % recall).
2. **Physics gate dependency:** The gate is conservative — it may suppress valid WARNING predictions from very early-stage bearing defects where physical measurements are still within normal limits.
3. **CPU-only inference:** P50 ~1050 ms end-to-end. GPU deployment would reduce to under 100 ms.
4. **Missing-modality fallback:** If a sensor modality is unavailable, the meta-feature vector has missing entries. No graceful fallback is currently implemented.
5. **Single-scalar DT parameterisation:** The digital twin drives all five modalities with a single degradation parameter (d), preventing simulation of independently-progressing fault modes.
6. **Thermal dataset size:** Only 369 IR images — limited diversity of thermal fault types.

---

## 9. How to Run

```bash
# 1. Start the backend
cd backend
pip install -r requirements.txt
python run.py
# → http://127.0.0.1:8000  (docs at /docs)

# 2. Start the frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173

# 3. In MATLAB
run('matlab_client/motor_params_normal.m')   % choose scenario
start_ai_server()                            % starts backend if not running
% Then run the Simulink model
```
