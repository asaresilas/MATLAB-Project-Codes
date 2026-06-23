# Simulink Sensor Requirements for Digital Twin Prediction

To successfully integrate the Python AI backend with your MATLAB/Simulink model, the following sensors and parameters must be configured in your simulation.

## 1. Global Requirements (Comprehensive Diagnosis)

For the **Comprehensive Diagnostic Endpoint** (`/api/v1/diagnose/comprehensive`), your Simulink model must aggregate and send the following data packet every prediction cycle (e.g., every 1 second).

| Parameter | Simulink Source / Sensor | Unit | Data Type | Dimensions | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Current (L1, L2, L3)** | 3-Phase Current Sensors | Amps (A) | `double` | `[1000 x 3]` | Electrical signatures for Stator/Rotor faults. |
| **Vibration (X, Y, Z)** | Tri-axial Accelerometer | g (m/s²) | `double` | `[1000 x 3]` | Mechanical signatures for Bearing/Structural faults. |
| **Rotational Speed** | Encoder / Tachometer | RPM | `double` | `Scalar` | Normalization factor for AI inference. |
| **Torque** | Torque Transducer | Nm | `double` | `Scalar` | Loading condition for process-mode failure detection. |
| **Temperature** | Thermocouples (Amb/Body) | °C / K | `double` | `Scalar` (x2) | Thermal stress and degradation rate factors. |

---

## 2. Model-Specific Requirements

If calling individual model endpoints, ensure the specific data requirements below are met.

### 2.1. CWRU Bearing Model (Vibration)
*   **Sensor:** High-frequency Accelerometer (Drive End)
*   **Input Name:** `signal`
*   **Sampling Rate:** Recommended **12 kHz** or **48 kHz** (matches training data).
*   **Buffer Size:** **1000 samples** per request.
*   **Endpoint:** `/api/v1/predict/cwru`

### 2.2. NASA RUL Model (Vibration/Feature Based)
*   **Sensor:** Accelerometer
*   **Input Name:** `data` (Features) or `signal` (Raw) 
*   **Sampling Rate:** **20 kHz**.
*   **Buffer Size:** 
    *   **Raw Signal:** **36 values** (1 set of features) or **1080 values** (30 steps of 36 features).
    *   **WebSocket Engine:** Automatically handles windowing for `36`-feature inputs.
*   **Endpoint:** `/api/v1/predict/nasa`

### 2.3. Induction Motor Model (Vibration)
*   **Sensor:** Accelerometer
*   **Input Name:** `signal`
*   **Buffer Size:** **2048 samples**.
*   **Endpoint:** `/api/v1/predict/induction`

### 2.4. Current Signature Analysis (MCSA)
*   **Sensor:** Current Sensors (Phase A, B, C)
*   **Input Name:** `data`
*   **Buffer Size:** **1000 samples** x **3 phases**.
*   **Endpoint:** `/api/v1/predict/current`

### 2.5. CIA-1 Industrial Process Model
*   **Sensors:** 
    *   Air Temperature [K]
    *   Process Temperature [K]
    *   Rotational Speed [RPM]
    *   Torque [Nm]
    *   Tool Wear [min]
*   **Endpoint:** `/api/v1/predict/cia1`

### 2.6. Thermal Imaging Model
*   **Sensor:** Thermal Camera (IR)
*   **Input Name:** `image_base64`
*   **Format:** Base64 encoded JPEG/PNG image string.
*   **Endpoint:** `/api/v1/predict/thermal`

---

## 3. Simulink Implementation Tips

1.  **Buffer Block:** Use the **Buffer** block in Simulink to collect `1000` or `2048` samples before sending to the MATLAB Function block.
2.  **Rate Transition:** Ensure the API call runs at a slower rate (e.g., 1 Hz) than the simulation solver (e.g., 1 kHz) to avoid slowing down the simulation.
3.  **Data Typing:** Ensure all signals are converted to `double` before sending to the Python API.

```matlab
% Example MATLAB Client Call
data = struct();
data.vibration_signal = buffer_vibration; % [1x2048]
data.temperature = temp_C;
data.speed = rpm;

result = client.diagnose_comprehensive(data);
```
