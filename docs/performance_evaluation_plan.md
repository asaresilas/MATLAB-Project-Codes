# System Performance Evaluation Plan

This document outlines the strategy for evaluating the Digital Twin's diagnostic and prognostic performance under simulated fault conditions.

## 1. Objective
To quantify the accuracy, reliability, and speed of the AI models when interacting with the dynamic Simulink simulation, while ensuring zero data leakage between training and evaluation.

## 2. Methodology: Integrity-First Evaluation

We will treat the Simulink model as the "Ground Truth" generator. We invoke faults programmatically and measure if the AI detects them correctly and in time.

### Step 1: Fault Injection Strategy (Simulink)
We will create a **Test Scenario Script** in MATLAB that runs the simulation while injecting specific faults at known times.

| Scenario | Fault Type | Severity Profile | Duration |
| :--- | :--- | :--- | :--- |
| **S1** | Healthy Operation | None | 10s |
| **S2** | Sudden Bearing Fault | Step Change (0 -> High) | 10s |
| **S3** | Degrading Bearing | Ramp (Linear increase in vibration) | 60s |
| **S4** | Motor Overheating | Ramp (Temperature drift) | 60s |

### Step 2: Data Collection
The MATLAB client will log every request and response to a **Validation Dataset** (`validation_log.csv`).

*   **Inputs:** Vibration, Current, Temperature, Speed (from Simulink).
*   **Ground Truth:** The actual fault injected (known by the script).
*   **AI Prediction:** The fault class and probability returned by the API.
*   **Latency:** Time taken for the API to respond.

### Step 3: Performance Metrics

We will calculate the following standard metrics:

#### A. Diagnostic Metrics (Fault Classification)
1.  **Confusion Matrix:** A table showing predicted vs. actual faults.
    *   *True Positives (TP):* Correctly identified faults.
    *   *False Positives (FP):* False alarms (Healthy identified as Faulty).
    *   *False Negatives (FN):* Missed faults (Faulty identified as Healthy).
2.  **Accuracy:** `(TP + TN) / Total Predictions`
3.  **Precision:** `TP / (TP + FP)` (Reliability of alarms)
4.  **Recall:** `TP / (TP + FN)` (Sensitivity to faults)
5.  **F1-Score:** Harmonic mean of Precision and Recall.

#### B. Prognostic Metrics (RUL Estimation)
For the "Degrading Bearing" scenario (S3), we evaluate the Remaining Useful Life (RUL) prediction.

1.  **RMSE (Root Mean Square Error):** Average magnitude of error in RUL prediction.
    *   `sqrt(mean((Predicted_RUL - Actual_RUL)^2))`
2.  **MAPE (Mean Absolute Percentage Error):** Average percentage error.
    *   `mean(|(Predicted - Actual) / Actual|) * 100%`
3.  **Prognostic Horizon (PH):** The time difference between when the fault starts and when the prediction converges to the true value within a specific error bound (e.g., +/- 10%).
4.  **Temporal Integrity Check:** Ensuring that evaluation is performed on sequential data that chronologically follows the training set (to allow for real-world RUL validation).

#### C. System Metrics
1.  **Average Latency:** Mean time for API response (Target: < 50ms).
2.  **Throughput:** Maximum number of predictions per second.

## 3. Execution Plan

1.  **Create MATLAB Test Script:** Write `run_performance_test.m` to automate the scenarios.
2.  **Run Simulation:** Execute the script. It sends data to the API and records responses.
3.  **Analyze Results:** Use Python (`pandas`, `scikit-learn`) to read `validation_log.csv` and generate the metrics report.

## 4. Example Output (Visuals)

*   **Confusion Matrix Heatmap:** Visualizing misclassifications.
*   **RUL vs. Time Plot:** Plotting "Predicted RUL" against "True RUL" (ideally a diagonal line) as the fault degrades.
*   **Latency Histogram:** Distribution of response times.
