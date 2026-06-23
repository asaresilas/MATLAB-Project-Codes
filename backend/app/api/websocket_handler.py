"""
WebSocket Handler for Real-Time MATLAB/Simulink Integration
=============================================================

Data Flow:
  SIMULINK -> (sensor data via WebSocket)
           -> FastAPI WebSocket Endpoint
           -> Model Inference (Deep MLP or Fallback)
           -> SIMULINK <- (predictions + alerts)

Path: D:\\Silas Document\\UMaT\\Year 4\\Project work\\Matlab_Project codes\\backend\\app\\api\\websocket_handler.py
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
from datetime import datetime, timezone
import numpy as np
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import model registry (same as used in endpoints)
try:
    from app.services.model_registry import registry
    from app.services.thermal_service import thermal_service
except ImportError:
    logger.warning("Models or services not available yet")
    registry = None
    thermal_service = None

# Database persistence — optional; non-fatal if DB is unavailable
try:
    from app.database import SessionLocal, SensorReading
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    logger.warning("database module not importable — sensor readings will NOT be persisted")

# ─── Meta Fusion Model Path (Relative to Project Root) ──────────────────────────
import os as _os
_project_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", ".."))
_META_MODEL_PATH = _os.path.join(_project_root, "Trained_models", "meta_fusion", "meta_fusion_xgb.pkl")

# Create router for WebSocket endpoints (no prefix — WebSocket paths are absolute)
router = APIRouter(tags=["websocket"])

# Separate router for the REST fallback endpoint
rest_router = APIRouter(prefix="/api/v1", tags=["simulink_rest"])

# ============================================================================
# CONNECTION MANAGER - Handles multiple simultaneous MATLAB clients
# ============================================================================

import re as _re
_CLIENT_ID_RE = _re.compile(r'^[A-Za-z0-9_\-]{1,64}$')

def _validate_client_id(client_id: str) -> bool:
    """Return True only for safe alphanumeric client IDs (prevents key injection)."""
    return bool(_CLIENT_ID_RE.match(client_id))


class ConnectionManager:
    """Manages WebSocket connections from multiple MATLAB/Simulink clients."""

    def __init__(self):
        # Active connections: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        self.dashboard_connections: List[WebSocket] = []
        # Client metadata: {client_id: {name, connected_at, samples_received, predictions_sent}}
        self.client_metadata: Dict[str, Dict[str, Any]] = {}
        # Async lock — prevents race conditions when multiple coroutines mutate the dicts
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str, client_name: str = None):
        """Register a new MATLAB client connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = {
            "name": client_name or f"MATLAB-{client_id}",
            "connected_at": datetime.now().isoformat(),
            "samples_received": 0,
            "predictions_sent": 0,
            "last_prediction_time_ms": 0,
            "status": "connected"
        }
        logger.info(f"✓ Client connected: {client_id} ({self.client_metadata[client_id]['name']})")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_confirmed",
            "client_id": client_id,
            "message": f"Connected to Predictive Maintenance API",
            "timestamp": datetime.now().isoformat()
        })
    
    async def disconnect(self, client_id: str):
        """Unregister a MATLAB client connection."""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
        if client_id in self.client_metadata:
            meta = self.client_metadata[client_id]
            logger.info(
                "✗ Client disconnected: %s  (received=%d  sent=%d)",
                client_id, meta.get("samples_received", 0), meta.get("predictions_sent", 0),
            )
    
    async def broadcast(self, message: dict, exclude_client: str = None):
        """Send message to all connected clients (except optionally one)."""
        async with self._lock:
            snapshot = dict(self.active_connections)
        disconnected = []
        for client_id, connection in snapshot.items():
            if exclude_client and client_id == exclude_client:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                disconnected.append(client_id)
        for client_id in disconnected:
            await self.disconnect(client_id)
            
    async def broadcast_dashboard(self, message: dict):
        """Send live predictions to all connected Dashboards."""
        disconnected = []
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to dashboard: {e}")
                disconnected.append(connection)
        for connection in disconnected:
            self.dashboard_connections.remove(connection)
    
    def get_client_info(self, client_id: str = None) -> Dict[str, Any]:
        """Get info about a specific client or all clients."""
        if client_id:
            return self.client_metadata.get(client_id, {})
        return self.client_metadata
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


# ── Module-level inference helper ─────────────────────────────────────────────

def _get_mc_prediction(model_obj, input_data, n_iter: int = 1):
    """Run model inference.

    Uses model.predict() (compiled, optimized graph) for the common n_iter=1
    case (deterministic forward pass).  When n_iter > 1 and the model has
    Dropout layers it switches to training=True calls for MC Dropout.

    Returns:
        (mean_pred, std_pred) — both numpy arrays with the same shape as
        a single model.predict() output.
    """
    if n_iter <= 1:
        # Fast path: compiled predict graph — 10–50× faster than eager mode.
        try:
            res = model_obj.predict(input_data, verbose=0)
            return res, np.zeros_like(res)
        except Exception as exc:
            logger.warning("model.predict() failed (%s) — falling back to eager call", exc)
            try:
                res = model_obj(input_data, training=False).numpy()
                return res, np.zeros_like(res)
            except Exception as exc2:
                logger.error("Inference completely failed: %s", exc2)
                raise
    else:
        # MC Dropout path (n_iter > 1): eager mode with training=True.
        try:
            preds = [model_obj(input_data, training=True).numpy() for _ in range(n_iter)]
            arr = np.array(preds)
            return np.mean(arr, axis=0), np.std(arr, axis=0)
        except Exception as exc:
            logger.warning("MC forward pass failed (%s) — using deterministic predict()", exc)
            res = model_obj.predict(input_data, verbose=0)
            return res, np.zeros_like(res)


def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ── Temperature unit conversion ───────────────────────────────────────────────
# MATLAB/Simulink always outputs temperatures in Kelvin (K).
# The backend, dashboard, database, and report all expect degrees Celsius (°C).
# Subtract 273.15 at every point where a raw scalar temperature is first read.
_KELVIN_OFFSET = 273.15

def _k_to_c(val: float) -> float:
    """Convert a Kelvin value from MATLAB to degrees Celsius."""
    return val - _KELVIN_OFFSET


def _persist_sensor_reading(
    client_id: str,
    machine_id: str,
    sensor_payload: Any,
    prediction_result: Dict[str, Any],
) -> None:
    """
    Write one sensor reading + its prediction outcome to the database.

    Each physical sensor measurement gets its own column so you can query and
    filter by RPM, temperature, vibration, etc. directly in DB Browser or SQL.

    Columns saved:
      rpm, torque_nm                  — mechanical operating point
      temp_motor_c, temp_ambient_c    — thermal readings  [°C]
      vib_rms, vib_peak, vib_samples  — vibration stats   [g]
      ia_rms, ib_rms, ic_rms          — 3-phase currents  [A]
      has_thermal                     — thermal camera present
      health_state                    — NORMAL/WARNING/CRITICAL/UNKNOWN
      confidence, uncertainty         — AI prediction quality
      rul_hours                       — Remaining Useful Life [hours]

    This is called via asyncio.to_thread() so it never blocks the event loop.
    All errors are swallowed so a DB failure never disrupts the prediction path.
    """
    if not _DB_AVAILABLE:
        return
    try:
        # ── Defaults for all sensor columns ──────────────────────────────────
        rpm_val          = None
        torque_val       = None
        temp_motor_val   = None
        temp_ambient_val = None
        vib_rms_val      = None
        vib_peak_val     = None
        vib_samples_val  = None
        ia_rms_val       = None
        ib_rms_val       = None
        ic_rms_val       = None
        has_thermal_val  = False

        if isinstance(sensor_payload, dict):
            vib     = sensor_payload.get("vibration") or []
            curr    = sensor_payload.get("current")   or []
            scalars = sensor_payload.get("scalars")   or []

            # ── Mechanical scalars: [RPM, Torque, Temp_Motor, Temp_Amb] ──────
            # Order matches simulink_predictive_gateway.m:
            #   scalars = double([RPM; Torque; Temp_Motor; Temp_Amb])
            try:
                sc = [float(s) for s in scalars]
                if len(sc) > 0: rpm_val          = round(sc[0], 2)
                if len(sc) > 1: torque_val       = round(sc[1], 3)
                # MATLAB sends temperatures in Kelvin → convert to °C for DB columns
                if len(sc) > 2: temp_motor_val   = round(sc[2] - _KELVIN_OFFSET, 2)
                if len(sc) > 3: temp_ambient_val = round(sc[3] - _KELVIN_OFFSET, 2)
            except Exception:
                pass

            # ── Vibration stats (computed over 2048-sample window) ───────────
            try:
                vib_arr = np.array(vib, dtype=float).flatten()
                if vib_arr.size > 0:
                    vib_rms_val     = round(float(np.sqrt(np.mean(vib_arr ** 2))), 6)
                    vib_peak_val    = round(float(np.max(np.abs(vib_arr))), 6)
                    vib_samples_val = int(vib_arr.size)
            except Exception:
                vib_samples_val = len(vib) if isinstance(vib, list) else None

            # ── 3-Phase current RMS ──────────────────────────────────────────
            # curr is a list of rows, each row is [Ia, Ib, Ic]
            try:
                curr_arr = np.array(curr, dtype=float)
                if curr_arr.ndim == 2 and curr_arr.shape[1] >= 3:
                    ia_rms_val = round(float(np.sqrt(np.mean(curr_arr[:, 0] ** 2))), 6)
                    ib_rms_val = round(float(np.sqrt(np.mean(curr_arr[:, 1] ** 2))), 6)
                    ic_rms_val = round(float(np.sqrt(np.mean(curr_arr[:, 2] ** 2))), 6)
            except Exception:
                pass

            has_thermal_val = bool(sensor_payload.get("thermal_image"))

        else:
            # Legacy flat 1-D array path — extract what we can
            flat = sensor_payload if isinstance(sensor_payload, list) else []
            vib_samples_val = len(flat)

        # ── Compact JSON summary (for audit / full detail view) ───────────────
        summary = {
            "rpm":          rpm_val,
            "torque_nm":    torque_val,
            "temp_motor":   temp_motor_val,
            "temp_ambient": temp_ambient_val,
            "vib_rms":      vib_rms_val,
            "vib_peak":     vib_peak_val,
            "vib_samples":  vib_samples_val,
            "ia_rms":       ia_rms_val,
            "ib_rms":       ib_rms_val,
            "ic_rms":       ic_rms_val,
            "has_thermal":  has_thermal_val,
        }
        raw_json = json.dumps(summary)

        row = SensorReading(
            timestamp         = datetime.now(timezone.utc),
            client_id         = client_id,
            machine_id        = machine_id or "UNKNOWN",
            # Physical sensor columns
            rpm               = rpm_val,
            torque_nm         = torque_val,
            temp_motor_c      = temp_motor_val,
            temp_ambient_c    = temp_ambient_val,
            vib_rms           = vib_rms_val,
            vib_peak          = vib_peak_val,
            vib_samples       = vib_samples_val,
            ia_rms            = ia_rms_val,
            ib_rms            = ib_rms_val,
            ic_rms            = ic_rms_val,
            has_thermal       = has_thermal_val,
            # Compact JSON summary
            sensor_data_json  = raw_json,
            # AI prediction outputs
            health_state      = prediction_result.get("alert_level", "UNKNOWN"),
            confidence        = _coerce_float(prediction_result.get("confidence")),
            uncertainty       = _coerce_float(prediction_result.get("uncertainty")),
            rul_hours         = prediction_result.get("rul_hours"),
            model_used        = str(prediction_result.get("model_used", ""))[:512],
            inference_time_ms = _coerce_float(prediction_result.get("inference_time_ms")),
        )
        db = SessionLocal()
        try:
            db.add(row)
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Failed to persist sensor reading to DB: %s", exc)


def _normalize_scalar_inputs(sensor_payload: Any) -> Dict[str, float]:
    if isinstance(sensor_payload, dict):
        scalars = sensor_payload.get("scalars", []) or []
        raw_motor  = _coerce_float(scalars[2] if len(scalars) > 2 else None)
        raw_amb    = _coerce_float(scalars[3] if len(scalars) > 3 else None)
        return {
            "rpm":          _coerce_float(scalars[0] if len(scalars) > 0 else None),
            "torque":       _coerce_float(scalars[1] if len(scalars) > 1 else None),
            "motor_temp":   _k_to_c(raw_motor),   # MATLAB sends K → convert to °C
            "ambient_temp": _k_to_c(raw_amb),      # MATLAB sends K → convert to °C
        }

    flat = np.array(sensor_payload if sensor_payload is not None else [], dtype=np.float32).flatten()
    tail = flat[-4:] if flat.size >= 4 else np.zeros(4, dtype=np.float32)
    raw_motor  = _coerce_float(tail[2] if tail.size > 2 else None)
    raw_amb    = _coerce_float(tail[3] if tail.size > 3 else None)
    return {
        "rpm":          _coerce_float(tail[0] if tail.size > 0 else None),
        "torque":       _coerce_float(tail[1] if tail.size > 1 else None),
        "motor_temp":   _k_to_c(raw_motor),   # MATLAB sends K → convert to °C
        "ambient_temp": _k_to_c(raw_amb),      # MATLAB sends K → convert to °C
    }


def _summarize_sensor_payload(sensor_payload: Any) -> Dict[str, Any]:
    scalars = _normalize_scalar_inputs(sensor_payload)
    phase_currents = {"u": 0.0, "v": 0.0, "w": 0.0, "imbalance": 0.0}
    vibration = {"rms": 0.0, "crestFactor": 0.0, "kurtosis": 0.0, "severity": "Unknown"}
    thermal = {"state": "Unavailable", "hotSpot": scalars["motor_temp"]}

    if isinstance(sensor_payload, dict):
        curr = np.array(sensor_payload.get("current", []), dtype=np.float32)
        vib = np.array(sensor_payload.get("vibration", []), dtype=np.float32).flatten()

        if curr.size:
            if curr.ndim == 2 and curr.shape[1] >= 3:
                u = curr[:, 0]
                v = curr[:, 1]
                w = curr[:, 2]
            else:
                curr = curr.flatten()
                usable = curr[:3000]
                if usable.size >= 3000:
                    reshaped = usable.reshape(1000, 3)
                    u, v, w = reshaped[:, 0], reshaped[:, 1], reshaped[:, 2]
                else:
                    split = np.array_split(usable, 3)
                    u, v, w = split[0], split[1], split[2]
            rms_values = [float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0 for arr in (u, v, w)]
            avg_current = np.mean(rms_values) if np.mean(rms_values) else 1.0
            imbalance = (max(rms_values) - min(rms_values)) / avg_current * 100.0 if avg_current else 0.0
            phase_currents = {
                "u": round(rms_values[0], 3),
                "v": round(rms_values[1], 3),
                "w": round(rms_values[2], 3),
                "imbalance": round(float(imbalance), 3),
            }

        if vib.size:
            rms = float(np.sqrt(np.mean(np.square(vib))))
            peak = float(np.max(np.abs(vib))) if vib.size else 0.0
            std = float(np.std(vib)) + 1e-9
            mean = float(np.mean(vib))
            kurtosis = float(np.mean((vib - mean) ** 4) / (std ** 4)) if vib.size else 0.0
            crest_factor = peak / rms if rms else 0.0
            # ISO 10816-3 Zone B/C boundary: 5.0 g warn, Zone D: 8.0 g critical
            severity = "Critical" if rms > 8.0 else "Warning" if rms > 5.0 else "Normal"
            vibration = {
                "rms": round(rms, 3),
                "crestFactor": round(float(crest_factor), 3),
                "kurtosis": round(kurtosis, 3),
                "severity": severity,
            }

        if sensor_payload.get("thermal_image"):
            thermal["state"] = "Available"
    else:
        flat = np.array(sensor_payload if sensor_payload is not None else [], dtype=np.float32).flatten()
        if flat.size >= 1000:
            vib = flat[: min(2048, flat.size)]
            rms = float(np.sqrt(np.mean(np.square(vib))))
            peak = float(np.max(np.abs(vib))) if vib.size else 0.0
            vibration = {
                "rms": round(rms, 3),
                "crestFactor": round(peak / rms if rms else 0.0, 3),
                "kurtosis": 0.0,
                # ISO 10816-3: Zone B/C = 5 g warn, Zone D = 8 g critical
                "severity": "Critical" if rms > 8.0 else "Warning" if rms > 5.0 else "Normal",
            }

    # Bearing temperature: physics-based approximation.
    # Bearings run cooler than stator windings — approximately ambient + 60% of stator rise.
    # Formula: T_bearing ≈ T_ambient + 0.60 × (T_stator − T_ambient)
    # Source: IEC 60034-14 / thermal network modelling best practice.
    _amb = scalars["ambient_temp"]
    _sta = scalars["motor_temp"]
    _bearing_approx = round(max(_amb, _amb + 0.60 * (_sta - _amb)), 3)
    temperatures = {
        "stator":  round(_sta, 3),
        "bearing": _bearing_approx,
        "delta":   round(max(0.0, _sta - _amb), 3),
    }
    thermal["hotSpot"] = round(max(thermal["hotSpot"], temperatures["stator"]), 3)

    return {
        "phaseCurrent": phase_currents,
        "vibration": vibration,
        "temperature": temperatures,
        "thermal": thermal,
        "operatingPoint": {
            "rpm": round(scalars["rpm"], 3),
            "torque": round(scalars["torque"], 3),
            "ambient": round(scalars["ambient_temp"], 3),
            # Load classification based on rated torque 97.3 N·m (15 kW @ 1480 RPM)
            # High: >110% rated (>107 N·m), Nominal: 50–110% rated, Low: <50% rated (<48.7 N·m)
            "load": "High" if scalars["torque"] > 107.0 else "Nominal" if scalars["torque"] > 48.7 else "Low",
        },
    }


def _build_dashboard_payload(client_id: str, machine_id: str, sensor_payload: Any, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
    sensor_summary = _summarize_sensor_payload(sensor_payload)
    model_used = prediction_result.get("model_used", "UNAVAILABLE")
    confidence = _coerce_float(prediction_result.get("confidence"))
    uncertainty = _coerce_float(prediction_result.get("uncertainty"))
    prediction_value = _coerce_float(prediction_result.get("prediction"))
    alert_level = prediction_result.get("alert_level", "UNKNOWN")
    # Use real NASA RUL when available; fall back to class-based approximation
    rul_hours = _coerce_float(
        prediction_result.get("rul_hours"),
        default=round(max(0.0, (1.0 - prediction_value) * 20000.0), 2),
    )

    models = {
        "Fusion": {
            "availability": "available" if prediction_result.get("status") == "success" else prediction_result.get("status", "unknown"),
            "predictedClass": alert_level,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "latencyMs": _coerce_float(prediction_result.get("inference_time_ms")),
        }
    }

    # Extract true per-model predictions instead of inferring from strings
    modalities = prediction_result.get("modalities", [])
    mod_map = {mod["id"]: mod for mod in modalities}
    
    base_names = ["CWRU", "Induction", "NASA", "Current", "Thermal"]
    for name in base_names:
        if name in mod_map:
            mod = mod_map[name]
            models[name] = {
                "availability": "available",
                "predictedClass": mod.get("model", "Unknown"),
                "confidence": _coerce_float(mod.get("conf")),
                "uncertainty": _coerce_float(mod.get("unc")),
                "latencyMs": _coerce_float(prediction_result.get("inference_time_ms")),
            }
        else:
            models[name] = {
                "availability": "standby",
                "predictedClass": "No inference",
                "confidence": 0.0,
                "uncertainty": 0.0,
                "latencyMs": 0.0,
            }

    return {
        "type": "dashboard_update",
        "client_id": client_id,
        "machine_id": machine_id,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction_value,
        "alert_level": alert_level,
        "status": prediction_result.get("status", "unknown"),
        "model_used": model_used,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "inference_time_ms": _coerce_float(prediction_result.get("inference_time_ms")),
        "machine": {
            "machineId": machine_id,
            "healthState": alert_level,
            "rulHours": rul_hours,
            # Note: per-inference certainty is at the top-level "confidence" field.
            # The frontend reads payload.confidence (not payload.machine.confidence).
            "predictionCertainty": round(confidence, 4),
            "uncertainty": round(uncertainty, 4),
        },
        "sensors": {
            "phaseCurrent": sensor_summary["phaseCurrent"],
            "vibration": sensor_summary["vibration"],
            "temperature": sensor_summary["temperature"],
            "thermal": sensor_summary["thermal"],
        },
        "operatingPoint": sensor_summary["operatingPoint"],
        "models": models,
        "diagnostics": {
            "backendState": "healthy" if prediction_result.get("status") == "success" else prediction_result.get("status", "unknown"),
            "activeClients": manager.get_connection_count(),
            "lastPredictionTimeMs": _coerce_float(prediction_result.get("inference_time_ms")),
        },
    }


# ============================================================================
# DATA FLOW & PREDICTION ENGINE
# ============================================================================

class PredictionEngine:
    """Handles model inference — Meta Fusion primary, rule-based fallback."""
    
    def __init__(self):
        self.primary_model_name = "Meta Fusion XGBoost"
        self.fallback_model_name = "Rule-Based Worst-Case"
        self.last_error = None
        self.meta_model = None
        self._load_meta_model()

    def _load_meta_model(self):
        """Attempt to load the trained Meta Fusion model."""
        try:
            if _os.path.exists(_META_MODEL_PATH):
                import joblib
                self.meta_model = joblib.load(_META_MODEL_PATH)
                logger.info(f"✓ Meta Fusion XGBoost Model loaded from {_META_MODEL_PATH}")
            else:
                logger.warning(f"Meta Fusion model not found at {_META_MODEL_PATH}. Using rule-based fallback.")
        except Exception as e:
            logger.warning(f"Failed to load Meta Fusion model: {e}. Using rule-based fallback.")
            self.meta_model = None
    
    async def predict(self, sensor_data: np.ndarray) -> Dict[str, Any]:
        """
        Inference pipeline:
        1. Receive sensor data from MATLAB
        2. Normalize data
        3. Predict using primary model
        4. If fails, fall back to secondary model
        5. Return prediction results
        
        Args:
            sensor_data: numpy array or list of sensor readings
            
        Returns:
            Dict with:
            - prediction: float (0-1, probability of failure)
            - alert_level: str ("NORMAL", "WARNING", "CRITICAL")
            - model_used: str (which model was used)
            - inference_time_ms: float
            - confidence: float
            - uncertainty: float
        \"\"\"
        """
        start_time = datetime.now()
        
        try:
            if registry is None or not registry.is_loaded():
                logger.warning("Models not loaded yet, returning UNAVAILABLE status")
                return {
                    "prediction": 0.0,
                    "alert_level": "UNKNOWN",
                    "model_used": "SYSTEM_LOADING",
                    "inference_time_ms": 0.0,
                    "confidence": 0.0,
                    "status": "unavailable"
                }
            
            # -- Structured Payload Handling --
            if isinstance(sensor_data, dict):
                # The payload contains structured matrices: vibration, current, scalars
                vib_data = np.array(sensor_data.get('vibration', []), dtype=np.float32)
                curr_data = np.array(sensor_data.get('current', []), dtype=np.float32)
                scalars = sensor_data.get('scalars', [])
                
                # Combine predictions from available modalities
                predictions_list = []
                
                # 1. Evaluate Vibration Models (CWRU, Induction, NASA)
                if vib_data.size >= 1000:
                    model_c = registry.get_model("CWRU")
                    if model_c:
                        inp = vib_data[:1000].reshape(1, 1000, 1)
                        mean_pred, std_pred = _get_mc_prediction(model_c, inp)
                        idx = np.argmax(mean_pred[0])
                        p = np.array(mean_pred[0]).flatten()
                        if len(p) < 3: p = np.pad(p, (0, 3 - len(p)), mode='constant')
                        elif len(p) > 3: p = p[:3]
                        predictions_list.append({
                            "val": float(idx) / 3.0, 
                            "unc": float(np.mean(std_pred[0])), 
                            "model": f"CWRU-CNN ({['Normal', 'Inner', 'Ball', 'Outer'][idx]})",
                            "conf": float(mean_pred[0][idx]),
                            "probs": p,
                            "id": "CWRU"
                        })
                        
                if vib_data.size >= 2048:
                    model_i = registry.get_model("Induction_Motor")
                    if model_i:
                        inp = vib_data[:2048].reshape(1, 2048, 1)
                        mean_pred, std_pred = _get_mc_prediction(model_i, inp)
                        idx = np.argmax(mean_pred[0])
                        p = np.array(mean_pred[0]).flatten()
                        if len(p) < 3: p = np.pad(p, (0, 3 - len(p)), mode='constant')
                        elif len(p) > 3: p = p[:3]
                        predictions_list.append({
                            "val": float(idx) / 3.0, 
                            "unc": float(np.mean(std_pred[0])), 
                            "model": f"Induction-CNN ({['Healthy', 'D1', 'D2', 'Ring'][idx]})",
                            "conf": float(mean_pred[0][idx]),
                            "probs": p,
                            "id": "Induction"
                        })
                        
                # C. NASA RUL
                model_n = registry.get_model("NASA")
                scaler_n = registry.get_scaler("NASA")
                if model_n and scaler_n:
                    seq = None
                    if vib_data.size >= 2048:
                        v2k = vib_data[:2048]
                        rms = np.abs(np.sqrt(np.mean(v2k**2)))
                        mean = np.mean(v2k)
                        std = np.std(v2k) + 1e-9
                        kurt = np.mean((v2k - mean)**4) / (std**4)
                        skew = np.mean((v2k - mean)**3) / (std**3)
                        cf = np.max(np.abs(v2k)) / rms if rms > 0 else 0
                        feat_vec = [rms, mean, std, np.max(v2k), np.min(v2k), kurt, skew, np.max(v2k)-np.min(v2k), cf]
                        features_36 = np.array(feat_vec * 4).reshape(1, -1)
                        seq = np.repeat(scaler_n.transform(features_36), 30, axis=0).reshape(1, 30, 36).astype(np.float32)
                    elif len(scalars) == 36:
                        seq = np.repeat(scaler_n.transform(np.array(scalars).reshape(1, -1)), 30, axis=0).reshape(1, 30, 36).astype(np.float32)
                    
                    if seq is not None:
                        mean_pred, std_pred = _get_mc_prediction(model_n, seq)
                        rul = float(mean_pred[0][0])
                        # RUL thresholds aligned with frontend PARAM_META:
                        # NORMAL >150 h, WARNING 50–150 h, CRITICAL <50 h
                        p_n = np.zeros(3)
                        if rul > 150: p_n[0] = 0.8; p_n[1] = 0.15; p_n[2] = 0.05
                        elif rul > 50: p_n[0] = 0.1; p_n[1] = 0.8;  p_n[2] = 0.1
                        else:          p_n[0] = 0.05; p_n[1] = 0.15; p_n[2] = 0.8
                        
                        unc = float(std_pred[0][0]) / 10.0
                        predictions_list.append({
                            "val": rul / 100.0,
                            "unc": unc,
                            "model": "NASA-BiLSTM-RUL (Uncertainty-Aware)",
                            "conf": 1.0 / (1.0 + unc),
                            "probs": p_n,
                            "id": "NASA"
                        })

                # D. Thermal Modality
                thermal_img = sensor_data.get('thermal_image')
                if thermal_img and thermal_service:
                    res_t = thermal_service.process_and_predict(thermal_img)
                    if "error" not in res_t:
                        p_t = np.zeros(3)
                        if res_t['alert_level'] == 'NORMAL': p_t[0] = res_t['confidence']
                        elif res_t['alert_level'] == 'WARNING': p_t[1] = res_t['confidence']
                        else: p_t[2] = res_t['confidence']
                        p_t[p_t == 0] = (1.0 - res_t['confidence']) / 2.0
                        
                        predictions_list.append({
                            "val": 0.0 if res_t['alert_level'] == 'NORMAL' else 0.8 if res_t['alert_level'] == 'CRITICAL' else 0.5,
                            "unc": 1.0 - res_t['confidence'],
                            "model": f"Thermal-MobileNet ({res_t['predicted_class']})",
                            "conf": res_t['confidence'],
                            "probs": p_t,
                            "id": "Thermal"
                        })

                # 2. Evaluate Current Models
                if curr_data.size >= 3000:
                    model_curr = registry.get_model("Current_Signature")
                    scaler_curr = registry.get_scaler("Current_Signature")
                    if model_curr:
                        if len(curr_data.shape) == 2 and curr_data.shape[1] == 3:
                            inp = curr_data[:1000, :].reshape(1, 1000, 3).astype(np.float32)
                        else:
                            inp = curr_data.flatten()[:3000].reshape(1, 1000, 3).astype(np.float32)

                        # Apply global per-channel z-score normalisation
                        # (required by retrained model — prevents NaN in LayerNorm)
                        if scaler_curr is not None:
                            try:
                                inp_flat = inp.reshape(-1, 3)
                                inp_scaled = scaler_curr.transform(inp_flat)
                                inp = inp_scaled.reshape(1, 1000, 3).astype(np.float32)
                            except Exception as _se:
                                logger.debug("Current scaler failed (%s) — using raw input", _se)

                        pred = model_curr.predict(inp, verbose=0)
                        idx = np.argmax(pred[0])
                        p_c = np.array(pred[0]).flatten()
                        if len(p_c) < 3: p_c = np.pad(p_c, (0, 3 - len(p_c)), mode='constant')
                        elif len(p_c) > 3: p_c = p_c[:3]

                        # Label mapping: 0=Healthy, 1=Bearing-Fault, 2=Broken-Rotor-Bar
                        curr_label = ["Healthy", "Bearing-Fault", "Broken-Rotor-Bar"][min(idx, 2)]
                        predictions_list.append({
                            "val": float(idx) / 2.0,
                            "unc": 0.0,
                            "model": f"Current-CNN ({curr_label})",
                            "conf": float(pred[0][idx]),
                            "probs": p_c,
                            "id": "Current"
                        })

                # --- 2.5 SAFETY EXPERT: Analyze Scalars (Temperatures) ---
                if scalars and len(scalars) >= 4:
                    # MATLAB sends temperatures in Kelvin → convert to °C before comparing
                    motor_temp = float(scalars[2]) - _KELVIN_OFFSET
                    amb_temp   = float(scalars[3]) - _KELVIN_OFFSET
                    
                    p_s = np.array([1.0, 0.0, 0.0]) # Start Healthy
                    s_val = 0.0
                    
                    # Thermal Thresholds — IEC 60034-1 Class F insulation
                    # Stator winding: warn > 95 °C, critical > 120 °C
                    # Temperature rise (ΔT): warn > 50 K, critical > 70 K
                    if motor_temp > 120 or (motor_temp - amb_temp) > 70:
                        p_s = np.array([0.0, 0.0, 1.0]); s_val = 0.95
                        logger.warning(f"CRITICAL: High Motor Temp ({motor_temp:.1f} °C) — IEC 60034-1 Class F limit 155 °C")
                    elif motor_temp > 95 or (motor_temp - amb_temp) > 50:
                        p_s = np.array([0.0, 1.0, 0.0]); s_val = 0.5
                        logger.warning(f"WARNING: Elevated Motor Temp ({motor_temp:.1f} °C)")
                        
                    # Electrical Overload
                    if curr_data.size > 0:
                        rms_c = np.sqrt(np.mean(curr_data**2))
                        if rms_c > 35: # Injected Fault Threshold
                            p_s = np.array([0.0, 0.0, 1.0]); s_val = 0.99
                            logger.error(f"CRITICAL: Massive Current Draw ({rms_c:.2f}A)")

                    predictions_list.append({
                        "val": s_val,
                        "unc": 0.0,
                        "model": "SCALAR_SAFETY_EXPERT",
                        "conf": 1.0,
                        "probs": p_s,
                        "id": "Scalar"
                    })
                        
                # ── 3. Aggregate via Meta Fusion (28-Dimensional XGBoost) ──────
                if not predictions_list:
                    return {
                        "prediction": 0.0,
                        "alert_level": "UNKNOWN",
                        "model_used": "NONE (No Matching Modality)",
                        "inference_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                        "confidence": 0.0,
                        "uncertainty": 0.0,
                        "status": "unavailable"
                    }

                # Organize exact array order: CWRU, Induction, NASA, Current, Thermal, Scalar
                mod_map = {p["id"]: p["probs"] for p in predictions_list}
                ordered_mods = ["CWRU", "Induction", "NASA", "Current", "Thermal", "Scalar"]
                
                f = []
                prob_list = []
                for mod in ordered_mods:
                    # Provide neutral ground if modality is missing
                    p = mod_map.get(mod, np.ones(3)/3.0)
                    f.extend(p)
                    prob_list.append(p)
                    
                # Aggregated Meta-Features (6 Experts)
                mean_p = np.mean(prob_list, axis=0)
                var_p = np.var(prob_list, axis=0)
                f.extend(mean_p)
                f.extend(var_p)
                
                # Individual Entropy (6 Experts)
                for p in prob_list:
                    f.append(-np.sum(p * np.log(np.clip(p, 1e-7, 1.0))))
                    
                # Global Metadata
                max_conf_feature = np.max(mean_p)
                agreement_feature = -np.sum(mean_p * np.log(np.clip(mean_p, 1e-7, 1.0)))
                f.extend([max_conf_feature, agreement_feature])
                
                score_vec = np.array(f).reshape(1, -1) # Now 34-Dimensions

                fusion_mode = "Meta Fusion"
                # Only use XGBoost meta-fusion when at least 2 real modalities are present.
                # With fewer modalities the feature vector is mostly neutral [1/3,1/3,1/3]
                # priors — a distribution the XGBoost never saw in training, causing
                # unreliable (often CRITICAL) outputs. Fall back to rule-based instead.
                _real_modality_count = len(predictions_list)
                if self.meta_model is not None and _real_modality_count >= 2:
                    try:
                        # self.meta_model is now XGBoost Classifier exported as scikit-learn standard
                        class_idx = int(self.meta_model.predict(score_vec)[0])
                        probs = self.meta_model.predict_proba(score_vec)[0]
                        confidence = float(probs[class_idx])
                        alert = ["NORMAL", "WARNING", "CRITICAL"][class_idx]
                        val = float(class_idx) / 2.0
                        models_used = ", ".join(p["model"] for p in predictions_list)
                        uncertainty = 1.0 - confidence
                    except Exception as e:
                        logger.warning(f"Meta model inference failed: {e}. Falling back to rule-based.")
                        fusion_mode = "Rule-Based (fallback)"
                elif _real_modality_count < 2:
                    # Not enough real signals — use weighted vote of available predictors
                    logger.info(f"Only {_real_modality_count} modality available; using rule-based fusion.")
                    fusion_mode = "Rule-Based (single modality)"

                if fusion_mode in ("Rule-Based (fallback)", "Rule-Based (single modality)"):
                    worst = max(predictions_list, key=lambda x: x["val"])
                    val = worst["val"]
                    alert = "NORMAL" if val < 0.3 else ("WARNING" if val < 0.7 else "CRITICAL")
                    confidence = worst["conf"]
                    uncertainty = worst["unc"]
                    models_used = worst["model"]
                    fusion_mode = "Rule-Based (fallback)"

                # Extract real RUL hours from NASA modality when available.
                # Fallback: class-based linear approximation (NORMAL→20000h, CRITICAL→0h).
                rul_hours_out: Optional[float] = None
                for _p in predictions_list:
                    if _p["id"] == "NASA":
                        # val was stored as rul/100, so multiply back to hours
                        rul_hours_out = round(float(_p["val"]) * 100.0, 2)
                        break
                if rul_hours_out is None:
                    rul_hours_out = round(max(0.0, (1.0 - float(val)) * 20000.0), 2)

                # ── Fault code — explicit integer so MATLAB never parses strings ─────
                # 0=None/Unknown  1=Bearing  2=Stator  3=Rotor  4=Tool/Industrial  5=Thermal
                fault_code = 0
                for _p in predictions_list:
                    _m = _p.get("model", "")
                    if _p["id"] == "CWRU" and any(k in _m for k in ("Inner", "Ball", "Outer")):
                        fault_code = 1; break
                    if _p["id"] == "Current":
                        if "Stator" in _m: fault_code = 2; break
                        if "Rotor"  in _m: fault_code = 3; break
                    if _p["id"] == "CIA1" and alert != "NORMAL":
                        fault_code = 4; break
                    if _p["id"] == "Thermal" and alert != "NORMAL":
                        fault_code = 5; break

                return {
                    "prediction": round(float(val), 4),
                    "alert_level": alert,
                    "fault_code": fault_code,
                    "model_used": f"[{fusion_mode}] {models_used}",
                    "inference_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "confidence": round(confidence, 4),
                    "uncertainty": round(uncertainty, 4),
                    "rul_hours": rul_hours_out,
                    "status": "success",
                    "modalities": predictions_list
                }
                    
            else:
                # Legacy fallback for 1D arrays
                sensor_array = np.array(sensor_data, dtype=np.float32)
                num_features = sensor_array.shape[0] if len(sensor_array.shape) == 1 else sensor_array.shape[1]
                
                model_used       = "NONE"
                prediction_value = 0.0
                confidence       = 0.0
                uncertainty      = 0.0

            # 1. NASA RUL (Sequential Data)
            if sensor_array.shape == (30, 36) or (len(sensor_array.shape) == 1 and num_features == 36):
                model = registry.get_model("NASA")
                scaler = registry.get_scaler("NASA")
                if model and scaler:
                    if len(sensor_array.shape) == 1:
                        feat_vector = sensor_array.reshape(1, -1)
                        scaled = scaler.transform(feat_vector)
                        seq = np.repeat(scaled, 30, axis=0).reshape(1, 30, 36).astype(np.float32)
                    else:
                        seq = sensor_array.reshape(1, 30, 36).astype(np.float32)
                    
                    mean_pred, std_pred = _get_mc_prediction(model, seq)
                    prediction_value = float(mean_pred[0][0]) / 100.0
                    uncertainty = float(std_pred[0][0]) / 10.0 # Normalized scale
                    model_used = "NASA-BiLSTM-RUL (Uncertainty-Aware)"
                    confidence = 1.0 / (1.0 + uncertainty)
                
            # 2. CWRU Bearing (Vibration Signal - 1000 points)
            elif num_features == 1000:
                model = registry.get_model("CWRU")
                if model:
                    inp = sensor_array.reshape(1, 1000, 1).astype(np.float32)
                    mean_pred, std_pred = _get_mc_prediction(model, inp)
                    idx = np.argmax(mean_pred[0])
                    prediction_value = float(idx) / 3.0
                    uncertainty = float(np.mean(std_pred[0]))
                    model_used = f"CWRU-CNN ({['Normal', 'Inner', 'Ball', 'Outer'][idx]})"
                    confidence = float(mean_pred[0][idx])

            # 3. CIA1 (Industrial - 8 features)
            elif num_features == 8:
                model = registry.get_model("CIA1")
                if model:
                    inp = sensor_array.reshape(1, 8).astype(np.float32)
                    mean_pred, std_pred = _get_mc_prediction(model, inp)
                    idx = np.argmax(mean_pred[0])
                    prediction_value = float(idx) / 3.0
                    uncertainty = float(np.mean(std_pred[0]))
                    model_used = f"CIA1-MLP ({['No-Fail', 'Tool', 'Strain', 'Power'][idx]})"
                    confidence = float(mean_pred[0][idx])

            # 4. Induction Motor (2048 points)
            elif num_features == 2048:
                model = registry.get_model("Induction_Motor")
                if model:
                    inp = sensor_array.reshape(1, 2048, 1).astype(np.float32)
                    mean_pred, std_pred = _get_mc_prediction(model, inp)
                    idx = np.argmax(mean_pred[0])
                    prediction_value = float(idx) / 3.0
                    uncertainty = float(np.mean(std_pred[0]))
                    model_used = f"Induction-CNN ({['Healthy', 'D1', 'D2', 'Ring'][idx]})"
                    confidence = float(mean_pred[0][idx])

            # 5. Current Signature (3-phase current)
            elif num_features == 3000: # 1000x3
                model = registry.get_model("Current_Signature")
                if model:
                    inp = sensor_array.reshape(1, 1000, 3)
                    pred = model.predict(inp, verbose=0)
                    idx = np.argmax(pred[0])
                    prediction_value = float(idx) / 2.0
                    model_used = f"Current-CNN ({['Healthy', 'Stator', 'Rotor'][idx]})"
                    confidence = float(pred[0][idx])

            # Fallback if no specific modality matched
            if model_used == "NONE":
                inference_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                return {
                    "prediction": 0.0,
                    "alert_level": "UNKNOWN",
                    "model_used": "UNAVAILABLE",
                    "inference_time_ms": round(inference_time_ms, 2),
                    "confidence": 0.0,
                    "uncertainty": 0.0,
                    "status": "unavailable",
                    "error_message": "Data shape did not match any loaded model."
                }
            
            # Calculate alert level
            if prediction_value < 0.2:
                alert_level = "NORMAL"
            elif prediction_value < 0.6:
                alert_level = "WARNING"
            else:
                alert_level = "CRITICAL"
            
            # Calculate inference time
            inference_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "prediction": round(prediction_value, 4),
                "alert_level": alert_level,
                "model_used": model_used,
                "inference_time_ms": round(inference_time_ms, 2),
                "confidence": round(confidence, 4),
                "uncertainty": round(uncertainty, 4),
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Inference pipeline failed: {e}")
            self.last_error = str(e)
            
            # Deterministic safe error state (NO RANDOM DATA)
            inference_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "prediction": 0.0,
                "alert_level": "UNKNOWN",
                "model_used": "UNAVAILABLE",
                "inference_time_ms": round(inference_time_ms, 2),
                "confidence": 0.0,
                "status": "error",
                "error_message": str(e)
            }


# Global prediction engine
prediction_engine = PredictionEngine()


@rest_router.post("/predict/simulink")
async def predict_simulink_rest(data: Dict[str, Any]):
    """
    REST endpoint for MATLAB/Simulink prediction (HTTP Legacy Fallback).
    Used automatically when MATLAB < R2022a cannot use websocket().

    Accepts the same structured payload as the WebSocket handler:
      { "sensor_data": { "vibration": [...], "current": [[...]], "scalars": [...] } }

    Returns ALL fields that api_wrapper.m reads via isfield():
      alert_level, fault_code, confidence, uncertainty, rul_hours, timestamp

    IMPORTANT: Also broadcasts a dashboard_update to all connected frontend
    clients so the React dashboard shows live MATLAB data even when MATLAB
    uses the HTTP fallback path (not WebSocket).
    """
    # Normalize payload — MATLAB sends sensor_data nested; flat dicts are also accepted.
    sensor_data = data.get("sensor_data", data)
    machine_id  = data.get("machine_id", "MATLAB-HTTP")
    client_id   = data.get("client_id",  "http-fallback")

    result = await prediction_engine.predict(sensor_data)

    # ── Broadcast to all connected dashboard (React frontend) clients ──────────
    # This is the same call the WebSocket path makes. Without this, the frontend
    # never sees MATLAB data when MATLAB uses the HTTP fallback (older MATLAB).
    dashboard_payload = _build_dashboard_payload(
        client_id=client_id,
        machine_id=machine_id,
        sensor_payload=sensor_data,
        prediction_result=result,
    )
    await manager.broadcast_dashboard(dashboard_payload)

    # ── Persist to database (non-blocking) ────────────────────────────────────
    asyncio.create_task(
        asyncio.to_thread(
            _persist_sensor_reading,
            client_id,
            machine_id,
            sensor_data,
            result,
        )
    )

    return {
        "type":               "prediction",
        "prediction":         result["prediction"],
        "alert_level":        result["alert_level"],
        "fault_code":         result.get("fault_code", 0),        # 0=None 1=Bearing 2=Stator 3=Rotor 4=Tool 5=Thermal
        "model_used":         result["model_used"],
        "confidence":         result["confidence"],
        "uncertainty":        result.get("uncertainty", 0.0),
        "rul_hours":          result.get("rul_hours"),             # None = not determined; 0 = imminent failure
        "inference_time_ms":  result["inference_time_ms"],
        "timestamp":          datetime.now().isoformat(),
        "status":             result["status"],
    }


@rest_router.post("/predict/simulink/thermal")
async def predict_thermal_rest(data: Dict[str, Any]):
    """
    REST endpoint for thermal-camera image prediction (HTTP Legacy Fallback).
    Called by PredictiveMaintenanceClient.predict_thermal() when use_http_fallback=True.

    Accepts:
      { "image_base64": "<base64-encoded JPEG>", "machine_id": "..." }

    Returns:
      { "alert_level": "NORMAL"|"WARNING"|"CRITICAL",
        "predicted_class": "<class name>",
        "confidence": float }
    """
    image_base64 = data.get("image_base64") or data.get("image")

    if not image_base64:
        return {
            "alert_level":     "NORMAL",
            "predicted_class": "Unavailable",
            "confidence":      0.0,
            "status":          "no_image",
        }

    if thermal_service is None:
        return {
            "alert_level":     "NORMAL",
            "predicted_class": "Service unavailable",
            "confidence":      0.0,
            "status":          "service_unavailable",
        }

    try:
        result = thermal_service.process_and_predict(image_base64)
        if "error" in result:
            return {
                "alert_level":     "NORMAL",
                "predicted_class": "Error",
                "confidence":      0.0,
                "status":          "error",
                "error":           result["error"],
            }
        return result
    except Exception as exc:
        logger.warning("Thermal REST prediction failed: %s", exc)
        return {
            "alert_level":     "NORMAL",
            "predicted_class": "Error",
            "confidence":      0.0,
            "status":          "error",
            "error":           str(exc),
        }


# ============================================================================
# WEBSOCKET ENDPOINTS - Data flow paths from/to MATLAB
# ============================================================================

@router.websocket("/ws/simulink/{client_id}")
async def websocket_simulink_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for MATLAB Simulink real-time integration.
    
    PATH: ws://0.0.0.0:8000/ws/simulink/{client_id}
    PROTOCOL: WebSocket with JSON messages
    
    Expected message format from MATLAB:
    {
        "type": "sensor_data",
        "timestamp": "2026-02-12T10:30:45.123Z",
        "sensor_data": [0.5, 0.3, 0.8, ...],
        "sensor_names": ["Vibration_X", "Vibration_Y", ...],
        "machine_id": "MOTOR-001"
    }
    
    Response sent to MATLAB:
    {
        "type": "prediction",
        "prediction": 0.67,
        "alert_level": "WARNING",
        "inference_time_ms": 12.5,
        "model_used": "Deep MLP",
        "timestamp": "2026-02-12T10:30:45.138Z"
    }
    """
    
    # Validate client_id before accepting — prevents path-traversal / key injection.
    if not _validate_client_id(client_id):
        await websocket.close(code=1008, reason="Invalid client_id format")
        logger.warning("Rejected connection: invalid client_id '%s'", client_id)
        return

    client_name = f"Simulink-{client_id}"

    try:
        # 1. CONNECT: Register new client
        await manager.connect(websocket, client_id, client_name)
        
        # 2. MESSAGE LOOP: Receive data from MATLAB and send predictions
        while True:
            # Receive message from MATLAB
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Update client metadata
            manager.client_metadata[client_id]["samples_received"] += 1
            
            logger.info(f"→ Received from {client_id}: {data.get('type', 'unknown')}")
            
            # Handle different message types
            if data.get("type") == "sensor_data":
                
                # Extract sensor readings
                sensor_readings = data.get("sensor_data", [])
                sensor_names = data.get("sensor_names", [])
                machine_id = data.get("machine_id", "UNKNOWN")
                
                # Run inference
                prediction_result = await prediction_engine.predict(sensor_readings)
                
                # Prepare response to MATLAB.
                # ALL fields that api_wrapper.m reads via isfield() must be present here.
                # Missing fields cause silent fallback to 0 / default values in MATLAB.
                response = {
                    "type": "prediction",
                    "client_id": client_id,
                    "machine_id": machine_id,
                    "prediction": prediction_result["prediction"],
                    "alert_level": prediction_result["alert_level"],
                    "fault_code": prediction_result.get("fault_code", 0),   # 0=None 1=Bearing 2=Stator 3=Rotor 4=Tool 5=Thermal
                    "model_used": prediction_result["model_used"],
                    "confidence": prediction_result["confidence"],
                    "uncertainty": prediction_result.get("uncertainty", 0.0),
                    "rul_hours": prediction_result.get("rul_hours"),         # None = not determined; 0 = imminent failure
                    "inference_time_ms": prediction_result["inference_time_ms"],
                    "timestamp": datetime.now().isoformat(),
                    "status": prediction_result["status"],
                }

                # Log warning/critical alerts
                if prediction_result["alert_level"] in ["WARNING", "CRITICAL"]:
                    response["alert_message"] = (
                        f"⚠️  {prediction_result['alert_level']}: "
                        f"Failure probability {prediction_result['prediction']:.2%}"
                    )
                    logger.warning(response["alert_message"])

                # Send prediction back to MATLAB
                await websocket.send_json(response)

                # Broadcast live update to all dashboard clients
                await manager.broadcast_dashboard(_build_dashboard_payload(
                    client_id=client_id,
                    machine_id=machine_id,
                    sensor_payload=sensor_readings,
                    prediction_result=prediction_result,
                ))

                # Persist sensor reading + prediction concurrently (non-blocking)
                asyncio.create_task(
                    asyncio.to_thread(
                        _persist_sensor_reading,
                        client_id,
                        machine_id,
                        sensor_readings,
                        prediction_result,
                    )
                )

                manager.client_metadata[client_id]["predictions_sent"] += 1
                manager.client_metadata[client_id]["last_prediction_time_ms"] = prediction_result["inference_time_ms"]
                
            elif data.get("type") == "health_check":
                # Respond to health check from MATLAB
                await websocket.send_json({
                    "type": "health_check_response",
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "connections_active": manager.get_connection_count()
                })
            
            elif data.get("type") == "thermal_image":
                # Handle real-time thermal image from Simulink/MATLAB
                image_base64 = data.get("image_base64")
                if image_base64 and thermal_service:
                    result = thermal_service.process_and_predict(image_base64)
                    
                    if "error" in result:
                        await websocket.send_json({"type": "error", "message": result["error"]})
                    else:
                        result["client_id"] = client_id
                        result["machine_id"] = data.get("machine_id", "UNKNOWN")
                        await websocket.send_json(result)
                        manager.client_metadata[client_id]["predictions_sent"] += 1
                else:
                    await websocket.send_json({"type": "error", "message": "No image data or service unavailable"})

            elif data.get("type") == "ground_truth":
                # Receive actual failure data for model retraining
                # This will be used for weekly retraining pipeline
                actual_failure = data.get("actual_failure")
                logger.info(f"← Received ground truth from {client_id}: {actual_failure}")
                
                await websocket.send_json({
                    "type": "ground_truth_ack",
                    "status": "recorded",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from {client_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON format",
                "details": str(e)
            })
        except Exception as send_error:
            logger.error(f"Failed to send error message to {client_id}: {send_error}")
            pass
        await manager.disconnect(client_id)
    
    except Exception as e:
        logger.error(f"WebSocket error from {client_id}: {e}")
        await manager.disconnect(client_id)

@router.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint strictly for the Front-End Dashboard.
    It connects passively and receives multiplexed streams from Simulink pings.
    """
    await websocket.accept()
    manager.dashboard_connections.append(websocket)
    logger.info("✓ Dashboard UI connected to live stream")
    await websocket.send_json({
        "type": "connection_confirmed",
        "message": "Dashboard stream connected",
        "timestamp": datetime.now().isoformat(),
        "backend_state": "healthy",
        "active_clients": manager.get_connection_count()
    })
    try:
        while True:
            # Send a lightweight ping every 30 s to detect dead connections.
            # The dashboard echoes any received text; if it is silent we rely on
            # the WebSocket close frame arriving when the tab/process dies.
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # No message received — send a ping to check liveness.
                try:
                    await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
                except Exception:
                    break   # Connection is dead; fall through to cleanup
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in manager.dashboard_connections:
            manager.dashboard_connections.remove(websocket)
        logger.info("✗ Dashboard UI disconnected")

# ============================================================================
# MONITORING & MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/ws/status")
async def websocket_status():
    """Get status of all WebSocket connections."""
    return {
        "active_connections": manager.get_connection_count(),
        "clients": manager.get_client_info(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/ws/client/{client_id}/stats")
async def client_stats(client_id: str):
    """Get statistics for a specific MATLAB client."""
    from fastapi import Response
    info = manager.get_client_info(client_id)
    if not info:
        return Response(
            content=f'{{"detail":"Client {client_id} not found"}}',
            status_code=404,
            media_type="application/json",
        )
    return {"client_id": client_id, "info": info, "timestamp": datetime.now().isoformat()}


@router.post("/ws/client/{client_id}/disconnect")
async def disconnect_client(client_id: str):
    """Manually disconnect a MATLAB client."""
    from fastapi import Response
    if client_id not in manager.active_connections:
        return Response(
            content=f'{{"detail":"Client {client_id} not found"}}',
            status_code=404,
            media_type="application/json",
        )
    await manager.active_connections[client_id].close()
    await manager.disconnect(client_id)
    return {"status": "disconnected", "client_id": client_id}


# ============================================================================
# DATA FLOW DOCUMENTATION
# ============================================================================

"""
DATA FLOW PATHS
===============

1. SIMULINK → API (PREDICTION REQUEST)
   ────────────────────────────────────
   
   Path: 
   Simulink Model 
     ↓ (sensor data via WebSocket)
   ws://0.0.0.0:8000/ws/simulink/{client_id}
     ↓ (websocket_simulink_endpoint receives)
   PredictionEngine.predict()
     ↓ (TensorFlow inference)
   Model (Deep MLP or Fallback)
     ↓ (returns prediction)
   Response sent back via WebSocket
     ↓
   Simulink Model receives prediction
   
   
2. API → SIMULINK (PREDICTION RESPONSE)
   ──────────────────────────────────────
   
   Response format:
   {
       "type": "prediction",
       "prediction": 0.67,                    # Failure probability (0-1)
       "alert_level": "WARNING",              # NORMAL | WARNING | CRITICAL
       "model_used": "Deep MLP",
       "confidence": 0.94,
       "inference_time_ms": 12.5,
       "timestamp": "2026-02-12T10:30:45.138Z",
       "status": "success"
   }
   
   
3. SIMULINK → API (GROUND TRUTH FOR LEARNING)
   ────────────────────────────────────────────
   
   Path:
   Virtual System (generates failure data)
     ↓
   Simulink Model detects/records actual failure
     ↓ (sends ground truth via WebSocket)
   ws://0.0.0.0:8000/ws/simulink/{client_id}
     ↓ (websocket_simulink_endpoint receives)
   Message type: "ground_truth"
     ↓
   Data stored for weekly retraining pipeline
     ↓ (Sunday night)
   Retraining script aggregates all ground truth
     ↓
   New model trained and tested
     ↓
   A/B testing: 10% traffic to new model
     ↓
   If metrics improve → Promoted to 100%
   
   
4. COMPLETE ROUND-TRIP TIMING
   ───────────────────────────
   
   Simulink sends sensor data at 100Hz = every 10ms
   
   Timeline:
   T=0ms      | Simulink sends 100-sensor sample
   T=1-2ms    | Network latency
   T=2-3ms    | Queue/processing
   T=3-15ms   | Inference (target 1.2ms, observe real ~10-15ms)
   T=15-16ms  | Response generation
   T=16-18ms  | Network latency
   T=18ms     | Simulink receives prediction
   
   Target P95: <50ms ✓
   Actual: ~18-20ms
   
   
5. FILE STORAGE PATHS (FOR LEARNING)
   ──────────────────────────────────
   
   Sensor Readings Database:
   PostgreSQL at: localhost:5432/predictive_maintenance
   Table: sensor_readings
     - timestamp
     - client_id
     - machine_id
     - sensor_data (JSON)
     - sensor_names (JSON)
   
   
   Predictions Logged:
   PostgreSQL Table: predictions_log
     - timestamp
     - client_id
     - prediction_value
     - alert_level
     - model_used
     - inference_time_ms
   
   
   Ground Truth Collected:
   PostgreSQL Table: ground_truth
     - timestamp
     - client_id
     - machine_id
     - actual_failure (boolean)
     - failure_type (string)
     - days_to_failure
   
   
   Retraining Data Pipeline:
   /data/retraining/
     └─ weekly/
         ├─ 2026-02-16/
         │   ├─ sensor_data.csv
         │   ├─ ground_truth.csv
         │   └─ training_log.txt
         └─ current/
             ├─ train.csv
             ├─ test.csv
             └─ metrics.json
"""

