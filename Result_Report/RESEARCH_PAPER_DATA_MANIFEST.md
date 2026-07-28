# Research Paper Data Manifest

> All values in this document are **experimentally confirmed** from the 2026-05-27 full pipeline rerun.
> Never substitute, interpolate, or round values for publication without re-running the corresponding script.

---

## Datasets Used

| Dataset | Source | URL | Samples | Fs (Hz) | Fault Types |
|---------|--------|-----|---------|---------|-------------|
| CWRU Bearing | Case Western Reserve University | https://engineering.case.edu/bearingdatacenter | 600 | 12 000 | Normal / Inner Race / Ball / Outer Race |
| NASA IMS | NASA Ames Prognostics Center | https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/ | 984 files | 20 000 | Run-to-failure, 4 bearings |
| Mendeley Current Sig. | Mendeley Data | https://data.mendeley.com/datasets/h4kd5bfgqm/1 | 3-class | — | Healthy / Bearing Fault / Broken Rotor Bar |
| Treml Induction Motor | HDF5 format | Mendeley / Kaggle | 4-class | 10 000 | Healthy / D1 / D2 / Ring |
| Thermal IR Images | Real IR camera | (proprietary, 369 samples) | 369 | — | Normal / Warning / Critical thermal state |

---

## Expert Model Architectures

| Model | Input | Output | Key Parameters |
|-------|-------|--------|----------------|
| CWRU-CNN | (1, 1000, 1) | 4-class softmax | 1D Conv, trained on 12 kHz bearing data |
| Induction-CNN | (1, 2048, 1) | 4-class softmax | 1D Conv, 10 kHz induction motor vibration |
| NASA Bi-LSTM-Attn | (1, 30, 36) | scalar RUL (hours) | 9 NASA stats × 4 bearings = 36 features, window=30 |
| Current-CNN v5 | (1, 1000, 3) | 3-class softmax | StatisticsExtractor layer (mean/std/range/max/min per channel → 15 features) |
| Thermal-MobileNetV2 | base64 JPEG | 3-class softmax | Transfer learning from ImageNet |
| Meta-Fusion XGBoost | (1, 32) | 3-class softmax | StackingClassifier on 32-dim meta-feature vector |

---

## Meta-Feature Vector (32 dimensions)

Constructed per equation documented in `scripts/document_meta_features.py`:

| Dims | Content |
|------|---------|
| 0–2 | CWRU-CNN class probabilities (Normal / Inner / Ball / Outer → 3 classes remapped) |
| 3–5 | Induction-CNN class probabilities |
| 6–8 | NASA Bi-LSTM-Attn: RUL / normalized RUL / binary degradation flag |
| 9–11 | Current-CNN v5 class probabilities |
| 12–14 | Thermal-MobileNetV2 class probabilities |
| 15–19 | Scalar safety: motor_temp / amb_temp / vib_rms / curr_rms / delta_T |
| 20–24 | Per-modality Shannon entropy |
| 25–29 | Per-modality decision margin (max p − second-max p) |
| 30–31 | Inter-expert variance (σ²_p) and max probability across all experts |

---

## Key Confirmed Values for Paper Tables

### Table II — Per-Expert Real-Data Metrics

| Expert | Metric | Value | Dataset |
|--------|--------|-------|---------|
| CWRU-CNN | Accuracy | 100 % | CWRU held-out (3-class) |
| NASA Bi-LSTM-Attn | MAE | 1.354 h | NASA IMS chronological holdout |
| NASA Bi-LSTM-Attn | R² | 0.9964 | NASA IMS chronological holdout |
| Current-CNN v5 | Accuracy (holdout) | 87.93 % | Mendeley Current Signature |
| Current-CNN v5 | Accuracy (cache) | 89.50 % | Mendeley Current Signature |
| Induction-CNN | Accuracy | 53.33 % | Treml (temporal shift — 4-class model on 3-class test) |

### Table III — Meta-Fusion System Results (DT holdout, n=300)

| Class | Precision | Recall | F1 | n |
|-------|-----------|--------|----|---|
| NORMAL (0) | 0.960 | 0.888 | 0.922 | 107 |
| WARNING (1) | 0.841 | 0.898 | 0.869 | 118 |
| CRITICAL (2) | 0.893 | 0.893 | 0.893 | 75 |
| **Macro** | — | — | **0.8948** | 300 |

5-fold CV F1-macro: **0.9089 ± 0.0134** [95% CI: 0.8971, 0.9206]

### Table IV — Baseline Comparison

| Baseline | F1-macro | 95% CI | Accuracy |
|----------|----------|--------|----------|
| Majority class | 0.1882 | [0.1679, 0.2069] | 0.3933 |
| Unimodal CWRU-CNN | 0.1753 | [0.1552, 0.1950] | 0.3567 |
| Rule-based (max severity) | 0.3670 | [0.3278, 0.4074] | 0.4400 |
| Late fusion (mean probs) | 0.7455 | [0.6926, 0.7889] | 0.7567 |
| Early fusion (MLP, raw) | 0.8202 | [0.7753, 0.8624] | 0.8267 |
| **Meta-Fusion (ours)** | **0.9089** | **[0.8971, 0.9206]** | **0.9089** |

### Table V — Ablation Study (F1-macro when modality removed)

| Removed | F1-macro | 95% CI | Δ vs Full |
|---------|----------|--------|-----------|
| None (full model) | 0.9003 | [0.8616, 0.9342] | — |
| CWRU vibration | 0.8671 | [0.8270, 0.9029] | **−0.0332** |
| NASA RUL | 0.8796 | [0.8412, 0.9162] | −0.0207 |
| Induction Motor | 0.8808 | [0.8425, 0.9164] | −0.0195 |
| Thermal | 0.8886 | [0.8517, 0.9223] | −0.0118 |
| Current Signature | 0.8953 | [0.8577, 0.9300] | **−0.0050** |

### Table VII — Latency Breakdown (CPU-only, warm-start, single sample)

| Stage | P50 (ms) | P99 (ms) |
|-------|----------|----------|
| CWRU-CNN | 249.1 | 935.7 |
| Induction-CNN | 145.6 | 275.7 |
| NASA Bi-LSTM-Attn | 173.4 | 771.6 |
| Current-CNN | 138.8 | 390.3 |
| Thermal-MobileNetV2 | 303.8 | 855.4 |
| Meta-fusion XGBoost | 37.8 | 50.5 |
| Meta-feature extraction | 0.67 | 1.25 |
| **Full pipeline (P50 sum)** | **~1050** | — |

Hardware: AMD64 Family 23, 4-core/8-thread, 23.5 GB RAM, CPU-only (no GPU).

### Table VIII — Statistical Significance (McNemar's, continuity-corrected)

| Comparison | χ² | p-value | Significant? |
|------------|-----|---------|-------------|
| vs majority class | 777.09 | < 0.0001 | Yes |
| vs late fusion | 157.09 | < 0.0001 | Yes |
| vs CWRU single model | 930.47 | < 0.0001 | Yes |

---

## Calibration

- Method: Shannon entropy H(p) = −Σ p_i log(p_i) applied to meta-fusion 3-class softmax.
- Implementation: single deterministic forward pass (n_iter=1). NOT Monte Carlo Dropout.
- Optimal threshold θ* = 0.30 nats → 67 % coverage, F1 = 0.9773 on certain predictions.
- ECE (Expected Calibration Error) = 0.0567 — well-calibrated.

---

## Result File Locations

| Result | File |
|--------|------|
| Primary metrics | `results/publication_metrics/crossval_ci.json` |
| Single holdout | `results/publication_metrics/official_results.json` |
| RUL unit validation | `results/publication_metrics/rul_unit_validation.json` |
| Ablation study | `results/publication_metrics/ablation_proper.json` |
| Baseline comparison | `results/publication_metrics/correct_baselines.json` |
| Latency breakdown | `results/publication_metrics/latency_breakdown.json` |
| Calibration/uncertainty | `results/publication_metrics/uncertainty_analysis.json` |
| Source identity test | `results/publication_metrics/source_identity_ablation.json` |
| DT contribution | `results/publication_metrics/dt_contribution.json` |
| Meta-feature manifest | `results/publication_metrics/meta_feature_documentation.json` |
| NASA PHM08 scoring | `results/publication_metrics/nasa_phm08_scoring.json` |
| Bi-LSTM model metadata | `Trained_models/nasa_bilstm/Bi-LSTM-Attn_metadata.json` |
