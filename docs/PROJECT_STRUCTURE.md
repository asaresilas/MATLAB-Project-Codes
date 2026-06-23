# Complete Project Organization Guide

## Folder Structure Overview

```
Predictive-Maintenance-System/
│
├── 📄 README.md (Main entry point)
├── 📄 requirements.txt (Global dependencies)
├── 📄 deployment_config.json (Model configuration)
│
├── 📂 docs/ (All Documentation - START HERE!)
│   ├── 📄 INDEX.md (Documentation index)
│   ├── 📄 SETUP.md (15 min - Installation)
│   ├── 📄 QUICK_START.md (5 min - First run)
│   ├── 📄 TROUBLESHOOTING.md (Common issues)
│   │
│   ├── 📂 models/ (AI Model Documentation)
│   │   ├── 📄 MODEL_ARCHITECTURE.md ⭐ (MAIN - Read this first!)
│   │   │   └─ Explains all 6 models:
│   │   │     - 1D CNN (Signal classification)
│   │   │     - Bi-LSTM+Attention (RUL prediction)
│   │   │     - Deep MLP (Feature classification)
│   │   │     - AutoEncoder (Anomaly detection)
│   │   │     - Ensemble (Robust prediction)
│   │   │     - MobileNetV2 (Thermal imaging)
│   │   ├── 📄 DETAILED_SPECS.md (Hyperparameters, architecture diagrams)
│   │   ├── 📄 TRAINING_GUIDE.md (How to retrain)
│   │   └── 📄 FINE_TUNING.md (Optimization tips)
│   │
│   ├── 📂 datasets/ (Dataset Documentation)
│   │   ├── 📄 DATASET_DOCUMENTATION.md ⭐ (MAIN - Read this first!)
│   │   │   └─ Documents all 6 datasets:
│   │   │     - NASA (Turbofan RUL)
│   │   │     - CWRU (Bearing faults)
│   │   │     - CIA1 (Machine failures)
│   │   │     - Current Signature (Motor electrical)
│   │   │     - Induction Motor (Multimodal health)
│   │   │     - Thermal (IR images)
│   │   ├── 📄 NASA_DETAILED.md (NASA dataset deep dive)
│   │   ├── 📄 CWRU_DETAILED.md (CWRU dataset details)
│   │   ├── 📄 CIA1_DETAILED.md (CIA1 details)
│   │   └── ... (More datasets)
│   │
│   ├── 📂 api/ (API Documentation)
│   │   ├── 📄 API_REFERENCE.md (All endpoints)
│   │   ├── 📄 AUTH_GUIDE.md (OAuth2 authentication)
│   │   ├── 📄 EXAMPLES.md (Code examples)
│   │   └── 📄 ERROR_CODES.md (Error handling)
│   │
│   ├── 📂 deployment/ (Production Setup)
│   │   ├── 📄 DEPLOYMENT.md (Production checklist)
│   │   ├── 📄 DOCKER.md (Docker deployment)
│   │   ├── 📄 KUBERNETES.md (K8s setup)
│   │   ├── 📄 AWS_SETUP.md (AWS deployment)
│   │   └── 📄 MONITORING.md (Production monitoring)
│   │
│   ├── 📂 development/ (Developer Guides)
│   │   ├── 📄 DEVELOPMENT.md (Contributing)
│   │   ├── 📄 CODE_STRUCTURE.md (Architecture)
│   │   ├── 📄 TESTING.md (Test framework)
│   │   └── 📄 CI_CD.md (Continuous integration)
│   │
│   └── 📄 PROJECT_STRUCTURE.md (This file's sibling - folder hierarchy)
│
├── 📂 backend/ (FastAPI Web Server)
│   ├── 📄 README.md (Backend specific docs)
│   ├── 📄 requirements.txt (Backend dependencies)
│   ├── 📄 .env.example (Configuration template)
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── 📄 main.py ⭐ (Server entry point)
│   │   │
│   │   ├── 📂 routers/ (API Endpoints)
│   │   │   ├── diagnosis.py (Main diagnosis endpoint)
│   │   │   ├── auth.py (Authentication)
│   │   │   ├── models.py (Model info endpoint)
│   │   │   ├── health.py (Health check)
│   │   │   └── README.md
│   │   │
│   │   ├── 📂 services/ (Business Logic)
│   │   │   ├── model_registry.py (Model loading)
│   │   │   ├── diagnosis_engine.py (Diagnosis logic)
│   │   │   ├── auth_service.py (Authentication)
│   │   │   ├── preprocessing.py (Data cleaning)
│   │   │   └── README.md
│   │   │
│   │   ├── 📂 models/ (Pydantic Schemas)
│   │   │   ├── request.py (Input models)
│   │   │   ├── response.py (Output models)
│   │   │   ├── user.py (User models)
│   │   │   └── README.md
│   │   │
│   │   ├── 📂 core/ (Core Configuration)
│   │   │   ├── config.py (Settings loading)
│   │   │   ├── security.py (OAuth2 setup)
│   │   │   ├── database.py (DB connection)
│   │   │   └── README.md
│   │   │
│   │   └── 📂 utils/ (Utilities)
│   │       ├── validators.py (Input validation)
│   │       ├── exceptions.py (Custom errors)
│   │       ├── logging.py (Logging setup)
│   │       └── README.md
│   │
│   └── 📂 tests/ (Backend tests)
│       ├── test_api.py
│       └── README.md
│
├── 📂 data/ (Data storage)
│   ├── 📂 datasets/ (Training data)
│   │   ├── NASA/
│   │   │   ├── 📄 README.md (NASA data info)
│   │   │   ├── train_FD001.txt
│   │   │   ├── test_FD001.txt
│   │   │   └── ...
│   │   │
│   │   ├── CWRU/
│   │   │   ├── 📄 README.md
│   │   │   ├── Normal/
│   │   │   ├── Inner_Race_Fault/
│   │   │   ├── Outer_Race_Fault/
│   │   │   └── Ball_Fault/
│   │   │
│   │   ├── CIA1/
│   │   │   ├── 📄 README.md
│   │   │   └── ... (CSV data files)
│   │   │
│   │   ├── Current_Signature/
│   │   │   ├── 📄 README.md
│   │   │   └── ... (3-phase signals)
│   │   │
│   │   ├── Induction_Motor/
│   │   │   ├── 📄 README.md
│   │   │   └── ... (multimodal data)
│   │   │
│   │   └── Thermal/
│   │       ├── 📄 README.md
│   │       └── ... (thermal images')
│   │
│   ├── 📂 trained_models/ (Saved AI Models)
│   │   ├── best_model_1D_CNN.keras
│   │   ├── best_model_1D_CNN_REPORT.txt ⭐ (Model performance report)
│   │   ├── best_model_LSTM.keras
│   │   ├── best_model_LSTM_REPORT.txt
│   │   ├── best_model_MLP.keras
│   │   ├── best_model_MLP_REPORT.txt
│   │   ├── best_model_Autoencoder.keras
│   │   ├── best_model_Autoencoder_REPORT.txt
│   │   ├── best_model_Ensemble.keras
│   │   ├── best_model_Ensemble_REPORT.txt
│   │   ├── best_model_MobileNetV2.keras
│   │   ├── best_model_MobileNetV2_REPORT.txt
│   │   └── 📄 MODELS_INDEX.md (Index of all models)
│   │
│   └── 📂 scalers/ (Data normalization)
│       ├── nasa_scaler.pkl
│       ├── cwru_scaler.pkl
│       ├── cia1_scaler.pkl
│       ├── current_sig_scaler.pkl
│       ├── induction_scaler.pkl
│       └── 📄 README.md (Scaler documentation)
│
├── 📂 notebooks/ (Jupyter Analysis & Training)
│   ├── 📄 README.md (Notebook guide)
│   │
│   ├── 📂 01_exploration/
│   │   ├── 01_EDA_NASA.ipynb (NASA exploratory analysis)
│   │   ├── 02_EDA_CWRU.ipynb
│   │   ├── 03_EDA_CIA1.ipynb
│   │   ├── 04_EDA_CurrentSig.ipynb
│   │   ├── 05_EDA_InductionMotor.ipynb
│   │   └── 06_EDA_Thermal.ipynb
│   │
│   ├── 📂 02_preprocessing/
│   │   ├── 01_NASA_Preprocessing.ipynb
│   │   ├── 02_CWRU_Preprocessing.ipynb
│   │   └── ... (More preprocessing)
│   │
│   ├── 📂 03_model_training/
│   │   ├── 01_1D_CNN_Training.ipynb
│   │   ├── 02_LSTM_Attention_Training.ipynb
│   │   ├── 03_Deep_MLP_Training.ipynb
│   │   ├── 04_Autoencoder_Training.ipynb
│   │   ├── 05_Ensemble_Training.ipynb
│   │   └── 06_MobileNetV2_Transfer_Learning.ipynb
│   │
│   ├── 📂 04_evaluation/
│   │   ├── 01_Model_Comparison.ipynb
│   │   ├── 02_Performance_Analysis.ipynb
│   │   ├── 03_Error_Analysis.ipynb
│   │   └── 04_ROC_Curves.ipynb
│   │
│   └── 📂 05_visualization/
│       ├── 01_Results_Visualization.ipynb
│       ├── 02_Feature_Importance.ipynb
│       └── 03_Predictions_Timeline.ipynb
│
├── 📂 scripts/ (Automation Scripts)
│   ├── 📄 README.md (Scripts guide)
│   │
│   ├── 📂 training/
│   │   ├── 📄 README.md (Training documentation)
│   │   ├── train_all_models.py (Train all models)
│   │   ├── train_model.py (Train single model)
│   │   ├── train_nasa_rul.py (NASA specific)
│   │   ├── train_cwru_faults.py (CWRU specific)
│   │   ├── hyperparameter_tuning.py (AutoML tuning)
│   │   └── evaluate_models.py (Model evaluation)
│   │
│   ├── 📂 utilities/
│   │   ├── 📄 README.md (Utilities documentation)
│   │   ├── data_preprocessing.py (Data cleaning)
│   │   ├── feature_extraction.py (Feature engineering)
│   │   ├── model_converter.py (Format conversion)
│   │   ├── generate_reports.py (Report generation)
│   │   └── upload_to_server.py (Deploy models)
│   │
│   ├── 📂 maintenance/
│   │   ├── 📄 README.md
│   │   ├── backup_models.py (Backup routine)
│   │   ├── health_check.py (System health)
│   │   └── clean_cache.py (Clear cache)
│   │
│   └── 📂 development/
│       ├── 📄 README.md
│       ├── generate_test_data.py (Create synthetic data)
│       ├── profile_models.py (Performance profiling)
│       └── lint_code.py (Code quality)
│
├── 📂 tests/ (Comprehensive Testing)
│   ├── 📄 README.md (Testing guide)
│   ├── 📄 conftest.py (Pytest configuration)
│   ├── 📄 test_config.yaml (Test settings)
│   │
│   ├── 📂 unit/ (Unit tests)
│   │   ├── 📄 README.md
│   │   ├── test_models.py (Model loading tests)
│   │   ├── test_preprocessing.py (Data processing tests)
│   │   ├── test_validators.py (Validation tests)
│   │   └── test_auth.py (Authentication tests)
│   │
│   ├── 📂 integration/ (Integration tests)
│   │   ├── 📄 README.md
│   │   ├── test_api_endpoints.py (API testing)
│   │   ├── test_diagnosis_flow.py (Diagnosis workflow)
│   │   ├── test_model_integration.py (Model loading)
│   │   └── test_auth_flow.py (Auth workflow)
│   │
│   ├── 📂 performance/ (Performance tests)
│   │   ├── 📄 README.md
│   │   ├── test_api_latency.py (Response time)
│   │   ├── test_model_inference_speed.py (Model speed)
│   │   ├── test_memory_usage.py (Memory profiling)
│   │   ├── test_concurrent_requests.py (Concurrency)
│   │   └── load_test_results.md (Results)
│   │
│   └── 📂 smoke/ (Quick validation)
│       ├── 📄 README.md
│       ├── quick_test.py (5 min validation)
│       └── test_all_models_loaded.py (Model check)
│
├── 📂 server/ (Server Management)
│   ├── 📄 README.md (Server guide)
│   │
│   ├── 📂 startup/
│   │   ├── 📄 README.md (Startup guide)
│   │   ├── START_API_SERVER.bat (Windows batch)
│   │   ├── START_API_SERVER.ps1 (PowerShell)
│   │   ├── start_server.sh (Linux/Mac shell)
│   │   ├── run_api_test.py ⭐ (Main test launcher)
│   │   └── health_check.py (Verify running)
│   │
│   ├── 📂 config/
│   │   ├── 📄 README.md (Configuration guide)
│   │   ├── deployment_config.json (Model paths & names)
│   │   ├── server_settings.yaml (Server options)
│   │   ├── logging_config.yaml (Logging setup)
│   │   └── security_settings.yaml (Security config)
│   │
│   ├── 📂 monitoring/
│   │   ├── prometheus_config.yaml (Prometheus setup)
│   │   ├── grafana_dashboard.json (Grafana dashboard)
│   │   └── alerts.yaml (Alert rules)
│   │
│   └── 📂 docker/
│       ├── Dockerfile (Docker image)
│       ├── docker-compose.yml (Multi-container)
│       └── .dockerignore
│
├── 📂 server_testing/ (API Testing Suite)
│   ├── 📄 README.md (Testing guide)
│   │
│   ├── 📂 api_tests/
│   │   ├── 📄 README.md (Test overview)
│   │   ├── test_api_professional.py ⭐ (Main professional test)
│   │   ├── test_all_models.py (Model verification)
│   │   ├── test_api_simple.py (Simple test)
│   │   ├── test_performance.py (Performance test)
│   │   └── test_results/ (Test outputs)
│   │
│   ├── API_PERFORMANCE_TEST_GUIDE.md (Detailed test guide)
│   └── test_reports/ (Historical reports)
│
├── 📂 MATLAB/ (MATLAB Integration)
│   ├── 📄 README.md (MATLAB guide)
│   ├── 📄 INSTALLATION.md (Setup MATLAB interface)
│   │
│   ├── 📄 PredictiveMaintenanceAPI.m ⭐ (Main client class)
│   │
│   ├── 📄 example_usage.m (Simple example)
│   ├── 📄 advanced_example.m (Complex example)
│   ├── 📄 motor_ar_view.m (3D visualization)
│   ├── 📄 time_travel_prognostics.m (Scenario analysis)
│   │
│   └── 📂 + (Plus symbolic link to current symlink)
│       ├── Simulink_Integration.slx (Simulink model)
│       └── Simulink_README.md
│
├── 📂 .venv/ (Python Virtual Environment - DO NOT COMMIT)
│   └── (Dependencies installed here)
│
└── 📄 .gitignore (Files to exclude from git)

```

---

## 📊 File Purpose Summary

### Documentation Files (READ FIRST!)
| File | Purpose | Read Time |
|------|---------|-----------|
| `docs/models/MODEL_ARCHITECTURE.md` | Explain all 6 models⭐ | 30 min |
| `docs/datasets/DATASET_DOCUMENTATION.md` | Explain all 6 datasets⭐ | 20 min |
| `docs/SETUP.md` | Installation guide | 15 min |
| `docs/QUICK_START.md` | 5 min first run | 5 min |
| `docs/api/API_REFERENCE.md` | API endpoints | 10 min |

### Data Report Files (CRITICAL!)
| File | Purpose |
|------|---------|
| `data/trained_models/*_REPORT.txt` | Model performance details |
| `data/datasets/*/README.md` | Dataset information |
| `data/scalers/README.md` | Normalization info |

### Executable Scripts
| File | Purpose |
|------|---------|
| `run_api_test.py` | Main test command ✓ |
| `server/startup/START_API_SERVER.*` | Start server |
| `scripts/training/train_all_models.py` | Train models |

---

## 🎯 How to Use This Structure

### For New Users:
1. Read: [`docs/QUICK_START.md`](docs/QUICK_START.md)
2. Run: `python run_api_test.py`
3. Read: [`docs/models/MODEL_ARCHITECTURE.md`](docs/models/MODEL_ARCHITECTURE.md)

### For Developers:
1. Study: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
2. Explore: `backend/app/` code structure
3. Run tests: `pytest tests/`

### For Data Scientists:
1. Explore: `notebooks/` for analysis
2. Read: [`docs/datasets/DATASET_DOCUMENTATION.md`](docs/datasets/DATASET_DOCUMENTATION.md)
3. Run: `scripts/training/train_all_models.py`

### For DevOps/Operations:
1. Read: [`docs/deployment/DEPLOYMENT.md`](docs/deployment/DEPLOYMENT.md)
2. Reference: `server/config/` for configuration
3. Monitor: `server/monitoring/` for setup

---

## 📝 Key Design Principles

✅ **Clear Organization**: Files grouped by function  
✅ **Comprehensive Documentation**: Each folder has README  
✅ **Report Files**: Performance metrics in text files  
✅ **Easy Discovery**: README.md files guide navigation  
✅ **Scalable Structure**: Room for growth  
✅ **Standard Layout**: Follows Python/ML best practices  

---

**Status**: Production Ready  
**Last Updated**: February 12, 2026
