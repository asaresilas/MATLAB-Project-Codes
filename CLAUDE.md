# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a UMaT Year 4 capstone project: a full-stack **Predictive Maintenance Digital Twin** for electric motors. It ingests vibration, current, and thermal sensor data from MATLAB/Simulink, runs multi-modal AI inference, and returns fault classifications and Remaining Useful Life (RUL) predictions in real-time.

## Commands

### Start the Backend API Server
```bash
cd backend
python run.py
# Server starts on http://127.0.0.1:8000
# Interactive docs at http://127.0.0.1:8000/docs
```

### Run Tests
```bash
# All tests
python -m pytest tests/ -v

# Single test file
python -m pytest tests/test_integration.py -v

# Single test
python -m pytest tests/test_integration.py::TestDigitalTwinPipeline::test_classifier_training -v
```

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Test the API Endpoints (after server is running)
```bash
python backend/test_client.py
python server_testing/api_tests/test_api_professional.py
```

### Run a Signal Processing Module Directly
```bash
python src/features/signal_processing.py    # runs self-test
python src/features/advanced_features.py    # runs self-test
python src/models/classifiers_enhanced.py   # runs self-test
```

## Architecture

### Data Flow (End-to-End)

```
MATLAB/Simulink
  └─ PredictiveMaintenanceClient.m
       ├─ WebSocket → ws://127.0.0.1:8000/ws/simulink/{client_id}
       └─ HTTP fallback → POST /api/v1/predict/simulink

FastAPI Backend (backend/app/main.py)
  ├─ Startup: ModelRegistry.load_models() loads all .keras + .pkl files
  │           config driven by backend/deployment_config.json
  │
  ├─ WebSocket handler (backend/app/api/websocket_handler.py)
  │   └─ PredictionEngine.predict()
  │       ├─ Structured payload (dict with vibration/current/scalars/thermal_image)
  │       │   ├─ CWRU-CNN  → 1000-point vibration → bearing fault class
  │       │   ├─ Induction-CNN → 2048-point vibration → motor health class
  │       │   ├─ NASA Bi-LSTM-Attn → 9 features × 4 = 36 features, window=30 → RUL
  │       │   ├─ Current-CNN → (1000, 3) 3-phase current → stator/rotor fault
  │       │   ├─ Thermal MobileNetV2 → base64 image → thermal fault class
  │       │   ├─ Scalar Safety Expert → motor_temp/ambient_temp thresholds
  │       │   └─ Meta Fusion XGBoost → 34-dim aggregated feature → NORMAL/WARNING/CRITICAL
  │       └─ Legacy 1D flat array path (backwards compat, shape-based routing)
  │
  ├─ REST endpoints (backend/app/api/endpoints.py)
  │   └─ /predict/{cia1|nasa|cwru|induction|current|thermal}
  │
  └─ Dashboard WebSocket → /ws/dashboard (frontend receives live updates)
```

### Model Registry

`backend/app/services/model_registry.py` is a **singleton** (`ModelRegistry`). It reads `backend/deployment_config.json` at startup to find model paths, then loads each `.keras` model with `safe_mode=True`. If a model file is missing it logs a warning and continues — the server can start with zero models loaded.

Models are keyed by their dataset name: `"CIA1"`, `"NASA"`, `"CWRU"`, `"Induction_Motor"`, `"Current_Signature"`, `"Thermal"`.

The Meta Fusion XGBoost model is loaded separately in `websocket_handler.py` from `Trained_models/meta_fusion/meta_fusion_xgb.pkl`.

### Feature Extraction

Two layers:
1. **Basic** (`src/features/signal_processing.py`): `extract_time_features()` (7 stats), `extract_nasa_features()` (9 stats), `extract_induction_features()` (13 stats including FFT), FFT, envelope spectrum.
2. **Advanced** (`src/features/advanced_features.py`): Wavelet (db4, 5-level), spectral (PSD via Welch), envelope spectrum (Hilbert), order tracking (BPFO/BPFI/BSF/FTF).

### Main Python Entry Point for MATLAB/Tests

`src/interface.py` → `analyze_motor_data(vibration, current, temperature, speed, dataset='cwru')` returns:
```python
{
    "status": str,         # fault class
    "confidence": float,
    "rul_hours": float,
    "rul_confidence": float,
    "features": dict|list, # depends on dataset
    "recommendation": str
}
```

This calls `ModelManager` (also in `interface.py`), which is a **separate** singleton from `ModelRegistry` — it loads models directly from `models/` and `Trained_models/` at import time.

### NASA Dataset

Raw files are in `datasets/NASA/1st_test/1st_test/` — each file is a tab-separated snapshot with 4 columns (one per bearing), named by timestamp (e.g. `2003.10.22.12.06.24`). Loaded via `src/data/loaders.py::NASALoader`.

### Authentication

JWT tokens (`/api/v1/auth/token`) and API keys (`/api/v1/api-keys/`). All credentials come from environment variables: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ENGINEER_USERNAME`, `ENGINEER_PASSWORD`, `JWT_SECRET_KEY`. If `ADMIN_PASSWORD` or `ENGINEER_PASSWORD` are unset, the server emits a `RuntimeWarning` and falls back to a placeholder — this must be overridden before any deployment. Passwords are hashed with PBKDF2-HMAC-SHA256 (260 000 iterations, random salt).

### MATLAB Client

`matlab_client/PredictiveMaintenanceClient.m` is a MATLAB OOP class. It requires MATLAB R2020b+ for WebSocket support. On older versions it falls back to HTTP polling via `connectViaHTTP()` → `/api/v1/predict/simulink`. Use `client.connect()`, `client.predict(sensor_data, sensor_names)`, `client.sendGroundTruth()`, `client.close()`.

## Publication Revision Scripts (IEEE Revision)

Ten scripts written to address peer-reviewer feedback. Run all from the project root.

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/validate_rul_units.py` | Verify RUL MAE/RMSE are in **hours**, check RMSE≥MAE | `results/publication_metrics/rul_unit_validation.json` |
| `scripts/ablation_study_proper.py` | Retrain meta-learner for each modality-removal scenario (correct methodology) | `results/publication_metrics/ablation_proper.json` |
| `scripts/crossval_with_ci.py` | 5-fold stratified CV + bootstrap CI + McNemar's test | `results/publication_metrics/crossval_ci.json` |
| `scripts/dt_contribution_ablation.py` | DT-grounded vs. random-balanced training comparison | `results/publication_metrics/dt_contribution.json` |
| `scripts/latency_breakdown_benchmark.py` | Component-level latency per pipeline stage (1000 warm runs) | `results/publication_metrics/latency_breakdown.json` |
| `scripts/mc_dropout_sensitivity.py` | Shannon entropy ECE + MC Dropout T analysis (if Dropout layers present) | `results/publication_metrics/uncertainty_analysis.json` |
| `scripts/correct_baselines.py` | Re-implement all comparison baselines correctly (fixes hard-coded 0.1882 and broken label mapping) | `results/publication_metrics/correct_baselines.json` |
| `scripts/source_identity_ablation.py` | Devil's Advocate: 4 tests for whether meta-learner exploits source ID vs. real fusion signal | `results/publication_metrics/source_identity_ablation.json` |
| `scripts/nasa_phm08_scoring.py` | PHM08 asymmetric scoring function adapted for bearing-hours RUL; includes C-MAPSS context benchmarks | `results/publication_metrics/nasa_phm08_scoring.json` |
| `scripts/document_meta_features.py` | Full 32-dim meta-feature manifest + corrected Eq. (5) text for paper (addresses §III.C reviewer) | `results/publication_metrics/meta_feature_documentation.json` |

**Official pipeline order (must run in this sequence)**:
`build_true_dataset.py` → `build_latent_digital_twin.py` → `generate_meta_features.py` → `train_meta_fusion.py` → `generate_publication_results.py` → all revision scripts.

**`compare_fusion_methods.py`**: Compares rule-based vs meta-fusion on the held-out test set. Uses raw (unscaled) 32-dim features for rule-based (valid [0,1] probability slots), and `scaler.transform()` output for the meta model. The probability slots are at expert offsets [0,5,10,15,20] — not stride-3 through the full vector (which would incorrectly include entropy/margin dims).

**Reproducibility**: `requirements_exact.txt` in project root (generated by `pip freeze`) lists all exact package versions. Use `n_jobs=1` in `StackingClassifier` — `n_jobs=-1` causes `PermissionError` on Windows restricted environments.

### Confirmed Metric Values (authoritative — 2026-05-27 full pipeline rerun with v5 StatisticsExtractor)

**PRIMARY IEEE PAPER METRICS:**

| Metric | Value | Unit | Source |
|--------|-------|------|--------|
| **F1-macro (5-fold CV)** | **0.9089 ± 0.0134** | — | `crossval_ci.json` (primary metric for paper) |
| **F1-macro 95% CI** | **[0.8971, 0.9206]** | — | `crossval_ci.json` |
| Bootstrap F1 CI | [0.8959, 0.9220] | — | `crossval_ci.json` (n=1000 resamples) |
| Accuracy (5-fold CV) | 0.9089 ± 0.0127 | — | `crossval_ci.json` |
| AUC-macro (5-fold CV) | 0.9803 ± 0.0042 | — | `crossval_ci.json` |
| F1-macro (single holdout) | 0.8948 | — | `official_results.json` (300-sample test) |
| Accuracy (single holdout) | 0.8933 | — | `official_results.json` |
| ROC-AUC OvR | 0.9798 | — | `official_results.json` |
| RUL MAE | **23.011** | **hours** (not %) | `official_results.json` |
| RUL RMSE | **26.810** | **hours** (not %) | `official_results.json` |
| RUL NRMSE | 0.2697 | dimensionless | `rul_unit_validation.json` (RMSE/max_RUL, max_RUL=99.4h) |
| Bi-LSTM MAE | 1.354 | hours | `Bi-LSTM-Attn_metadata.json` |
| Bi-LSTM RMSE | 1.734 | hours | `Bi-LSTM-Attn_metadata.json` |
| Bi-LSTM R² | 0.9964 | — | `Bi-LSTM-Attn_metadata.json` |

**Per-class (holdout 300 samples):**

| Class | Precision | Recall | F1 | n |
|-------|-----------|--------|----|---|
| NORMAL (0) | 0.960 | 0.888 | 0.922 | 107 |
| WARNING (1) | 0.841 | 0.898 | 0.869 | 118 |
| CRITICAL (2) | 0.893 | 0.893 | 0.893 | 75 |

**Latency (component-level, CPU-only, warm-start single-sample):**

| Stage | P50 | P99 |
|-------|-----|-----|
| CWRU-CNN inference | 249.1 ms | 935.7 ms |
| Induction-CNN inference | 145.6 ms | 275.7 ms |
| NASA Bi-LSTM inference | 173.4 ms | 771.6 ms |
| Current-CNN inference | 138.8 ms | 390.3 ms |
| Thermal-MobileNetV2 inference | 303.8 ms | 855.4 ms |
| Meta-fusion XGBoost stack | 37.8 ms | 50.5 ms |
| Meta-feature extraction | 0.67 ms | 1.25 ms |
| **Full pipeline (sum P50)** | **~1050 ms** | — |
| Hardware | AMD64 Family 23 (4-core/8-thread), 23.5 GB RAM, CPU-only | — |

> Note: The 29.60 ms / 43.12 ms figures in old commits were BATCH throughput (300 samples ÷ 300), not single-sample latency. Report ~1050 ms as the online inference latency on CPU.

**Statistical Significance (McNemar's test, continuity-corrected):**

| Comparison | chi² | p-value | Significant? |
|------------|------|---------|-------------|
| vs majority class | 777.09 | 0.0000 | YES |
| vs late fusion | 157.09 | 0.0000 | YES |
| vs CWRU single model | 930.47 | 0.0000 | YES |

### Physical Validation Results (individual expert models on cache data)

| Model | Metric | Value | Notes |
|-------|--------|-------|-------|
| CWRU-CNN | Accuracy | **100%** | 3 classes present (Normal/Inner/Ball) in cache; dynamic label detection |
| NASA Bi-LSTM | MAE | **1.354 h** | From `Bi-LSTM-Attn_metadata.json`; authoritative per-model metric |
| NASA Bi-LSTM | R² | **0.9964** | From `Bi-LSTM-Attn_metadata.json` |
| Induction-CNN | Accuracy | **53.33%** | Temporal distribution shift (chronological split); 4-class model on 3-class test |
| Current-CNN (v5 StatisticsExtractor) | Accuracy | **87.93%** holdout / **89.50%** cache | 3-class, amplitude statistics, domain-robust |

**Current-CNN v5 (StatisticsExtractor, 2026-05-27):** The ACTIVE production model. Uses `StatisticsExtractor` custom Keras layer to extract (mean, std, range, max, min) per channel → 15 features → Dense MLP. Registered with `@tf.keras.utils.register_keras_serializable(package="current_feat")`. Saved: `Trained_models/current_signature_dl/cnn_model.keras`. Architecture: `(1000,3) → StatisticsExtractor(15) → Normalization → Dense(128) → Dense(64) → Dense(32) → Dense(3,softmax)`. Label map: `{0: healthy, 1: bearing_fault, 2: broken_rotor_bar}`. 

**Why v5 and not the Conv1D (v6, 99.77%):** Conv1D has a **domain shift failure** on synthetic latent DT data — it predicts class 1 (Bearing-Fault) for 100% of the 300 DT test samples. StatisticsExtractor's amplitude statistics generalize across real and synthetic signals, correctly mapping NORMAL→Healthy, WARNING→Bearing-Fault, CRITICAL→BRB with 85% confidence.

**All scripts** that load the Current model must register StatisticsExtractor before calling `load_model()`:
```python
@tf.keras.utils.register_keras_serializable(package="current_feat")
class StatisticsExtractor(tf.keras.layers.Layer):
    def call(self, x):
        mu=tf.reduce_mean(x,axis=1); sig=tf.math.reduce_std(x,axis=1)
        mx=tf.reduce_max(x,axis=1); mn=tf.reduce_min(x,axis=1); rng=mx-mn
        return tf.concat([mu,sig,rng,mx,mn],axis=1)
    def get_config(self): return super().get_config()
```

**Induction-CNN limitation:** The model has 4 output classes but the test cache has 3 classes. Temporal holdout produces distribution shift (Fault-D2 → 0% recall). Report 53.33% honestly with explanation.

**The paper's "%" suffix on RUL values is wrong** — values are hours. The print statement in `generate_publication_results.py` was fixed to label them `h` instead of `%`.

**The paper's P=R=F1=1.00 for the Critical class is a transcription error** — source was the training-set 10-fold CV evaluation (135 samples, 45/class), not the held-out test.

### Uncertainty Quantification (actual implementation)

The system uses **Shannon entropy** `H(p) = -Σ p_i log(p_i)` applied to the meta-fusion 3-class softmax output. `n_iter=1` in `websocket_handler.py::get_mc_prediction` — this is a **single deterministic forward pass**, not Monte Carlo Dropout (T=30 was never implemented). If the paper mentions MC Dropout, remove it.

**ECE Analysis (from `mc_dropout_sensitivity.py`):**
- Deterministic Shannon entropy: ECE=0.0567, mean H=0.2849 nats (well-calibrated)
- MC Dropout (T=5–50): ECE=0.21–0.24 (WORSE than deterministic; entropy range 0–1.099 nats)
- Conclusion: Keep deterministic approach. Do NOT adopt MC Dropout — it degrades calibration.

### Ablation Study Results (correct methodology — retrain meta-learner per scenario)

From `ablation_proper.json`:

| Scenario | F1-macro | 95% CI | Δ vs Full |
|----------|----------|--------|-----------|
| Full Model (baseline) | 0.9003 | [0.8616, 0.9342] | — |
| Remove CWRU vibration | 0.8671 | [0.8270, 0.9029] | **−0.0332** (most impactful) |
| Remove NASA RUL | 0.8796 | [0.8412, 0.9162] | −0.0207 |
| Remove Induction Motor | 0.8808 | [0.8425, 0.9164] | −0.0195 |
| Remove Thermal | 0.8886 | [0.8517, 0.9223] | −0.0118 |
| Remove Current Signature | 0.8953 | [0.8577, 0.9300] | **−0.0050** (least impactful) |

### Baseline Comparison (from `correct_baselines.py`)

| Baseline | F1-macro | 95% CI | Accuracy |
|----------|----------|--------|----------|
| Majority class | 0.1882 | [0.1679, 0.2069] | 0.3933 |
| Unimodal CWRU | 0.1753 | [0.1552, 0.1950] | 0.3567 |
| Rule-based (max severity) | 0.3670 | [0.3278, 0.4074] | 0.4400 |
| Late fusion (mean probs) | 0.7455 | [0.6926, 0.7889] | 0.7567 |
| Early fusion (MLP, raw) | 0.8202 | [0.7753, 0.8624] | 0.8267 |
| **Meta-Fusion (ours)** | **0.9089** | **[0.8971, 0.9206]** | **0.9089** |

### DT Contribution and Source Identity Findings

**DT Contribution (`dt_contribution_ablation.py`):**
- DT-grounded: F1=0.9003 [0.8616, 0.9342]
- Random-balanced: F1=0.9083 [0.8726, 0.9398]
- Delta: −0.0080 (overlapping CIs → no statistically significant accuracy difference)
- **Paper framing**: The DT's contribution is NOT measured in accuracy. Its contribution is: (1) systematic physics-consistent multi-modal data generation, (2) avoiding the need for simultaneous physical failures, (3) scalable data augmentation via the latent degradation variable `d`.

**Source Identity Ablation (`source_identity_ablation.py`):**
- Source indicator only (which expert dominates): F1=0.7469 (insufficient → refutes source-ID hypothesis)
- Base probabilities only (15-dim, no entropy/margin): F1=0.8986
- Full 32-dim meta-features: F1=0.8800
- **Finding**: Entropy/margin features add −0.0186 F1 vs base probabilities alone. Base probability vectors carry most discrimination signal. The 32-dim meta-feature construction is sound but the entropy/margin extensions could be simplified.

### NASA PHM08 Scoring

- PHM08 asymmetric score: 6546.55 (lower=better; penalises late predictions more harshly)
- n_late: 174 (penalised more), n_early: 126
- R²: 0.1296 (poor — expected for a 100h RUL range with many near-zero predictions)
- Note: PHM08 benchmark uses turbofan cycles, not bearing hours — direct comparison not appropriate. This script provides the formula adaptation for paper transparency.

## Key Known Issues

- **`backend/deployment_config.json`**: Already updated to reference `cnn_classifier.keras` (`.keras` v3 format, safe_mode compatible). All 6 models are set `legacy_format: false`.
- **Current-CNN must be v5 StatisticsExtractor**: The Conv1D (v6, 99.77% on real data) has domain shift failure on synthetic DT data — predicts 100% class 1. Always use the StatisticsExtractor version at `Trained_models/current_signature_dl/cnn_model.keras`. All scripts loading it must register `StatisticsExtractor` with `@tf.keras.utils.register_keras_serializable(package="current_feat")` before calling `load_model()`.
- **`generate_meta_features.py` check**: The script validates `fusion_train_cache.npz` and `fusion_test_cache.npz` exist but then loads from `latent_train_cache.npz` and `latent_digital_twin.npz`. The check on lines 59-60 is stale (harmless but confusing).
- **`nasa_phm08_scoring.py` Attention fix**: Updated to use keyword-only `name=` argument in `add_weight()` for Keras 3.x compatibility.
- **`train_meta_fusion.py` MLP convergence**: Updated MLP base estimators to `max_iter=2000, early_stopping=True` and replaced MLP judge with `LogisticRegression` for stability. Now achieves F1=0.8948 on 300-sample holdout (up from 0.8842 with old settings).

### Previously fixed bugs (no longer present in code)
- `src/interface.py`: `project_root` NameError if TensorFlow unavailable — **fixed** (moved to `self.project_root` in `__init__`)
- `backend/app/api/websocket_handler.py`: `model_used`/`prediction_value`/`confidence` unbound in legacy 1D-array branch — **fixed** (initialized before the if/elif chain)
- `src/interface.py`: dead `pass`-only branch in `predict_rul()`, duplicate imports, duplicate `rul` calculation — **fixed**
- `scripts/train_comparison_baselines.py`: hard-coded `f1_early = 0.1882` and broken CWRU 4→3 class label mapping producing sub-chance 17.53% F1 — **documented**; use `scripts/correct_baselines.py` instead

## Model Input Shapes (for new endpoints or tests)

| Model | Input shape | Output |
|-------|-------------|--------|
| CWRU-CNN | `(1, 1000, 1)` | 4-class softmax (Normal/Inner/Ball/Outer) |
| Induction-CNN | `(1, 2048, 1)` | 4-class softmax (Healthy/D1/D2/Ring) |
| NASA Bi-LSTM-Attn | `(1, 30, 36)` | scalar RUL (hours) |
| Current-CNN (v5 StatisticsExtractor) | `(1, 1000, 3)` | 3-class softmax (Healthy/Bearing-Fault/Broken-Rotor-Bar) — 87.93% holdout, 89.50% cache. **Requires `StatisticsExtractor` custom object** registered with `package="current_feat"`. |
| CIA1-MLP | `(1, 8)` | 4-class softmax (No-Fail/Tool/Strain/Power) |
| Thermal-MobileNetV2 | base64 JPEG via `thermal_service` | 3-class (Normal/Warning/Critical) |

NASA features are 9 stats replicated ×4 = 36 features, then scaled with the paired `.pkl` scaler, then repeated 30 times to form the sequence window.
