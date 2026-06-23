# 🏭 Predictive Maintenance System with Digital Twin & MATLAB Integration

**Framework for Hierarchical Meta-Fusion in Industrial Systems**

## 📖 Introduction
This project presents a **framework for real-time health monitoring** and **Remaining Useful Life (RUL)** prediction of industrial motors using hierarchical meta-fusion of multi-modal sensor data. It bridges the gap between advanced **Deep Learning (AI)** models and standard **MATLAB/Simulink** engineering workflows.

This framework demonstrates the effectiveness of **digital twin-inspired latent state evaluation** for predictive maintenance systems.

---

## 🚀 Framework Overview

### Step 1: Multi-Modal AI Ensemble (Specialized Experts) 🧠
We developed **6 specialized AI models** to handle different types of sensor data in a digital-twin-inspired environment.
*   **Approach:** Trained on NASA, CWRU, and synthetic datasets to simulate various degradation patterns.
*   **The Models:**
    1.  **NASA Bi-LSTM:** Predicts RUL (Remaining Useful Life) using vibration history.
    2.  **CWRU CNN:** Detects *where* the bearing fault is (Inner, Outer, Ball).
    3.  **Induction Motor DL:** Analyzes overall motor health classes.
    4.  **Current Signature (MCSA):** Detects electrical stator/rotor faults.
    5.  **CIA-1 Hybrid:** Predicts industrial machine failure modes (Tool wear, etc.).
    6.  **Thermal Vision (MobileNetV2):** Classifies faults from heat maps.
*   **Methodology:** Implemented **Temporal Splitting** for NASA data and maintained rigorous evaluation protocols suitable for simulation-grounded validation.

### Step 2: Hierarchical Meta-Fusion (The Aggregator) ⚙️
The raw AI models produce specialized outputs that need intelligent combination.
*   **Our Contribution:** We created `src/interface.py` implementing hierarchical meta-fusion.
*   **How it works:**
    *   Accepts predictions from multiple specialized models.
    *   Applies learned uncertainty-weighted aggregation.
    *   Produces unified diagnostic assessment with confidence bounds.
    *   Translates technical outputs into actionable insights.

### Step 3: API Infrastructure (The Framework) 🌐
To enable integration with MATLAB/Simulink, we developed a service-oriented architecture.
*   **Implementation:** Built a **FastAPI** web server in `backend/app/main.py`.
*   **Architecture:**
    *   Provides "Comprehensive Diagnostic" endpoint (`/diagnose/comprehensive`).
    *   Enables any platform (MATLAB, Web, Simulation) to access fused predictions.
    *   **Validation:** Designed for simulation-grounded evaluation, not field deployment.

### Step 4: MATLAB & Simulink Integration (The Validation Environment) 📈
Core contribution: Demonstration of framework integration in simulation environments.
*   **Implementation:** MATLAB Client (`matlab_client/PredictiveMaintenanceAPI.m`).
*   **Validation Approach:**
    *   **Latency Testing:** Verified low-latency performance in simulation context.
    *   **Robustness Testing:** Validated consistent behavior under simulated disturbances.
    *   **Integration Testing:** Demonstrated seamless Simulink workflow integration.

### Step 5: Scientific Contributions (Framework Innovation) ✨
Key innovations presented in this framework:
*   **Uncertainty-Aware Fusion:** Combines model predictions with calibrated uncertainty estimates.
*   **Hierarchical Architecture:** Efficiently integrates multi-modal, multi-rate sensor data.
*   **Simulation-Grounded Validation:** Comprehensive evaluation in digital twin environment.

---

## 📂 File & Folder Structure (Framework Components)

Here is a map of the framework components and their specific functions:

| Folder / File | Description |
| :--- | :--- |
| **`backend/`** | **Service Infrastructure** |
| `├── app/main.py` | Core API service entry point. |
| `├── app/api/comprehensive.py` | Hierarchical fusion logic implementation. |
| `├── app/services/model_registry.py` | Model management and loading infrastructure. |
| **`src/`** | **Fusion Algorithm Implementation** |
| `├── interface.py` | Meta-fusion algorithm and uncertainty quantification. |
| **`matlab_client/`** | **Validation Environment** |
| `├── PredictiveMaintenanceAPI.m` | MATLAB integration layer for simulation validation. |
| `├── motor_ar_view.m` | Visualization for simulation results. |
| `├── example_usage.m` | Validation scenario demonstration. |
| **`Trained_models/`** | **Specialized AI Models** (Reference implementations) |

---

## 🛠️ Reproduction Instructions

### 1. Start the Service (Framework Core)
Open your terminal in the project folder and run:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
*Wait for "Application startup complete".*

### 2. Run Simulation Validation
1.  Open **MATLAB**.
2.  Navigate to the `matlab_client` folder.
3.  Open `example_usage.m`.
4.  **Run** the script.

**Expected Results:**
*   **Performance Metrics:** Diagnostic F1-Score of ~90.61% in simulation environment.
*   **Latency Characteristics:** P50 ~23.91ms, P99 ~43.65ms in controlled setting.
*   **Validation Output:** Real-time visualization of diagnostic decisions.

---

## 📊 Scientific Validation

1.  **Evaluation Framework:** Digital-twin-inspired latent state evaluation with physically-informed synthetic data.
2.  **Comparative Analysis:** Superior performance vs uni-modal, early fusion, and late fusion baselines (17.53% to 90.61% F1-Score).
3.  **Limitations:** Framework validated in simulation environment; field validation required for industrial deployment.

---
*Framework by [Silas Aasre] - Apr 2026*
*Simulation-Grounded Research Artifact*
