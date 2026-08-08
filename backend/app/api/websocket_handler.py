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
_META_MODEL_PATH  = _os.path.join(_project_root, "Trained_models", "meta_fusion", "meta_fusion_xgb.pkl")
_META_SCALER_PATH = _os.path.join(_project_root, "data", "meta_fusion_scaler.pkl")

# Feature-vector builder — must match training pipeline exactly
import sys as _sys
_src_path = _os.path.join(_project_root, "src")
if _src_path not in _sys.path:
    _sys.path.insert(0, _src_path)
try:
    from features.meta_fusion_features import extract_meta_features_from_predictions, build_nasa_probs
    _META_FEATURES_AVAILABLE = True
except ImportError as _e:
    logger.warning("meta_fusion_features not importable (%s) — feature vector will fall back to legacy layout", _e)
    _META_FEATURES_AVAILABLE = False

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
    """Convert a Kelvin value from MATLAB to degrees Celsius (always subtracts offset)."""
    return val - _KELVIN_OFFSET


def _auto_celsius(val: float) -> float:
    """Auto-detect K vs °C: val > 273 → Kelvin (subtract 273.15), else already Celsius.

    MATLAB motor_params_*.m files define both _K and _C variables.  The Simulink
    port can be wired to either.  Values > 273 are unambiguously Kelvin (no real
    motor operates at −0 °C); values ≤ 273 are already in °C.
    """
    return (val - _KELVIN_OFFSET) if val > 273 else val


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
                # MATLAB sends temperatures in K or °C — auto-detect to convert for DB columns
                if len(sc) > 2: temp_motor_val   = round(_auto_celsius(sc[2]), 2)
                if len(sc) > 3: temp_ambient_val = round(_auto_celsius(sc[3]), 2)
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
            "motor_temp":   _auto_celsius(raw_motor),   # auto-detect K vs °C
            "ambient_temp": _auto_celsius(raw_amb),     # auto-detect K vs °C
        }

    flat = np.array(sensor_payload if sensor_payload is not None else [], dtype=np.float32).flatten()
    tail = flat[-4:] if flat.size >= 4 else np.zeros(4, dtype=np.float32)
    raw_motor  = _coerce_float(tail[2] if tail.size > 2 else None)
    raw_amb    = _coerce_float(tail[3] if tail.size > 3 else None)
    return {
        "rpm":          _coerce_float(tail[0] if tail.size > 0 else None),
        "torque":       _coerce_float(tail[1] if tail.size > 1 else None),
        "motor_temp":   _auto_celsius(raw_motor),   # auto-detect K vs °C
        "ambient_temp": _auto_celsius(raw_amb),     # auto-detect K vs °C
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
            # api_wrapper.m already converts m/s² → g (divides by 9.81) before sending.
            # vib is therefore in g here — do NOT divide by 9.81 again.
            rms  = float(np.sqrt(np.mean(np.square(vib))))  # g (ISO 10816-3)
            peak = float(np.max(np.abs(vib))) if vib.size else 0.0  # g
            std = float(np.std(vib)) + 1e-9
            mean = float(np.mean(vib))
            kurtosis = float(np.mean((vib - mean) ** 4) / (std ** 4)) if vib.size else 0.0
            crest_factor = peak / rms if rms else 0.0
            # ISO 10816-3 Group II thresholds in g: Zone A<0.51, Zone B 0.51-2.04, Zone C-D >2.04
            severity = "Critical" if rms > 2.04 else "Warning" if rms > 0.51 else "Normal"
            vibration = {
                "rms": round(rms, 4),
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
            # Data arrives in g (api_wrapper divides by 9.81 before sending)
            rms  = float(np.sqrt(np.mean(np.square(vib))))   # g (ISO 10816-3)
            peak = float(np.max(np.abs(vib))) if vib.size else 0.0  # g
            vibration = {
                "rms": round(rms, 4),
                "crestFactor": round(peak / rms if rms else 0.0, 3),
                "kurtosis": 0.0,
                # ISO 10816-3 Group II thresholds in g: Zone A<0.51, Zone B 0.51-2.04
                "severity": "Critical" if rms > 2.04 else "Warning" if rms > 0.51 else "Normal",
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
            # Load classification based on rated torque 483.9 N·m (75 kW @ 1480 RPM)
            # High: >110% rated (>532 N·m), Nominal: 50–110% rated, Low: <50% rated (<242 N·m)
            "load": "High" if scalars["torque"] > 532.0 else "Nominal" if scalars["torque"] > 242.0 else "Low",
        },
    }


# ── Fault taxonomy ───────────────────────────────────────────────────────────
# Single source of truth for the fault bitmask, the operator explanation and the
# frontend fault list.  Bit VALUES are part of the MATLAB contract
# (simulink_predictive_gateway.m / api_wrapper.m) and must not be renumbered.
#
# Detector mapping is grounded in each dataset's own class semantics:
#   CWRU-CNN      Inner / Ball / Outer  → bearing race defects
#   Current-CNN   Bearing-Fault         → bearing;  Broken-Rotor-Bar → rotor cage
#   Induction-CNN D1 = bearing fault, D2 = stator fault, Ring = rotor end-ring
#                 (Treml et al. dataset definition — see references [13])
# Bit 2 is the STATOR winding fault. It was previously labelled "Shaft Fault"
# and fed from the Induction-CNN Ring class, which is a rotor end-ring defect,
# not a shaft defect — that mapping was incorrect on both counts.
F_BEARING = 1   # bit 0
F_ROTOR   = 2   # bit 1
F_STATOR  = 4   # bit 2
F_THERMAL = 8   # bit 3

_FAULT_CATALOG = [
    {
        "bit": F_BEARING, "code": 1, "name": "Bearing Fault",
        "component": "Drive-end rolling-element bearing",
        "description": (
            "Periodic impulsive energy at the bearing pass frequency indicates a "
            "rolling-element bearing defect on the outer race, inner race or a ball."),
        "action": (
            "Inspect and re-lubricate the drive-end bearing, and plan replacement "
            "within the next maintenance window."),
    },
    {
        "bit": F_ROTOR, "code": 2, "name": "Rotor Fault",
        "component": "Rotor cage (bars and end-ring)",
        "description": (
            "Current-signature asymmetry consistent with a broken rotor bar or a "
            "cracked end-ring, which produces sidebands around the supply frequency "
            "and increased torque ripple."),
        "action": (
            "Arrange an electrical rotor inspection; avoid sustained full-load "
            "operation until the rotor cage has been checked."),
    },
    {
        "bit": F_STATOR, "code": 3, "name": "Stator Winding Fault",
        "component": "Stator winding and insulation",
        "description": (
            "Vibration and current signatures consistent with stator winding "
            "asymmetry, such as an inter-turn short or early insulation degradation."),
        "action": (
            "Perform insulation-resistance and winding-balance tests before the "
            "next start; do not reset any protection trip without testing."),
    },
    {
        "bit": F_THERMAL, "code": 4, "name": "Thermal Fault",
        "component": "Stator winding temperature",
        "description": (
            "Winding temperature has exceeded the IEC 60034-1 Class F limits, which "
            "accelerates insulation ageing and shortens remaining life."),
        "action": (
            "Check cooling-air path, fan and ambient temperature, and reduce load "
            "until the winding temperature returns within limits."),
    },
]
_FAULT_BY_BIT = {f["bit"]: f for f in _FAULT_CATALOG}


def _build_fault_list(fault_flags: int, evidence: Dict[int, list],
                      motor_temp: float, vib_rms: float) -> list:
    """Expand the bitmask into an ordered, fully-described fault list.

    Each entry names one fault, explains it, states the evidence that raised it
    and gives the operator action — so a multi-fault state is never collapsed
    into an opaque "Multiple Faults" label.
    """
    out = []
    for spec in _FAULT_CATALOG:
        if not (fault_flags & spec["bit"]):
            continue
        detail = dict(spec)
        detail["evidence"] = evidence.get(spec["bit"], [])
        if spec["bit"] == F_THERMAL and motor_temp:
            detail["measurement"] = f"stator winding {motor_temp:.0f} °C"
        elif spec["bit"] == F_BEARING and vib_rms:
            detail["measurement"] = f"vibration RMS {vib_rms:.2f} g"
        out.append(detail)
    return out


def _compose_fault_name(faults: list) -> str:
    """Readable name for one or many simultaneous faults.

    Returns e.g. "Bearing Fault", or "Bearing + Thermal Fault" — never the
    opaque "Multiple Faults", which told the operator nothing.
    """
    if not faults:
        return "Healthy"
    if len(faults) == 1:
        return faults[0]["name"]
    stems = [f["name"].replace(" Fault", "") for f in faults]
    return " + ".join(stems) + " Fault"


def _generate_fault_explanation(alert_level: str, fault_type_name: str,
                                vib_rms: float, motor_temp: float,
                                rul_hours, confidence: float,
                                faults: Optional[list] = None) -> str:
    """Return a 2–3 sentence operator explanation for the current prediction."""
    # Multi-fault: name each fault and give severity-appropriate action.
    if faults and len(faults) > 1:
        vib_s  = f"{vib_rms:.2f}" if vib_rms else "—"
        temp_s = f"{motor_temp:.0f}" if motor_temp else "—"
        named  = "; ".join(f"{f['name']} ({f['component']})" for f in faults)
        if alert_level == "CRITICAL":
            closing = ("Stop the motor, apply lockout/tagout, and complete a full "
                       "inspection of every affected component before restart.")
        else:
            closing = ("Schedule a combined mechanical and electrical inspection "
                       "covering each affected component, and increase monitoring "
                       "frequency until it is carried out. The motor may continue to "
                       "run under supervision.")
        return (
            f"{len(faults)} simultaneous fault signatures were detected — {named}. "
            f"Vibration RMS is {vib_s} g and stator temperature is {temp_s} °C. "
            f"{closing}"
        )
    rul_str = f"{rul_hours:.0f}" if rul_hours is not None else "—"
    vib_str = f"{vib_rms:.2f}" if vib_rms else "—"
    temp_str = f"{motor_temp:.0f}" if motor_temp else "—"

    if alert_level == "NORMAL":
        return (
            f"All monitored parameters are within design limits for this squirrel-cage induction motor. "
            f"Vibration RMS is {vib_str} g (ISO 10816-3 Zone A), stator temperature is {temp_str} °C "
            f"(below 95 °C IEC Class F limit), and the Remaining Useful Life estimate is {rul_str} hours. "
            f"Continue normal operation."
        )
    if fault_type_name == "Bearing Fault":
        return (
            f"A developing bearing defect has been detected by the CWRU-CNN and Current-CNN modalities. "
            f"Vibration RMS of {vib_str} g indicates elevated impulsive energy consistent with an outer-race defect. "
            f"Schedule bearing inspection and lubrication check within the next maintenance window — do not defer beyond 72 hours of operation."
        )
    if fault_type_name == "Rotor Fault":
        return (
            f"The Induction-CNN and Current-CNN modalities have detected asymmetry consistent with a broken rotor bar or rotor misalignment. "
            f"Current imbalance and elevated torque ripple are indicative of rotor cage degradation. "
            f"Arrange an electrical and mechanical inspection; avoid sustained operation at full load until inspected."
        )
    if fault_type_name == "Shaft Fault":
        return (
            f"Shaft-related fault signatures (ring fault or shaft crack) have been detected by the Induction-CNN modality. "
            f"Elevated sub-synchronous vibration components are present in the vibration spectrum. "
            f"Perform an alignment check and visual shaft inspection at the next opportunity."
        )
    if fault_type_name == "Thermal Fault":
        return (
            f"Critical stator winding temperature of {temp_str} °C exceeds the IEC 60034-1 Class F absolute limit of 120 °C. "
            f"Continued operation risks irreversible insulation degradation and potential winding burnout. "
            f"Stop the motor immediately, implement lockout/tagout, and contact the site engineer before any restart."
        )
    if fault_type_name == "Multiple Faults":
        return (
            f"Multiple simultaneous fault signatures have been detected across the vibration, current, and thermal modalities. "
            f"Vibration RMS is {vib_str} g and stator temperature is {temp_str} °C — both elevated above healthy limits. "
            f"Stop the motor, implement lockout/tagout, and perform a full multi-disciplinary inspection before restart."
        )
    if alert_level == "WARNING":
        return (
            f"A developing fault condition has been detected. Vibration RMS is {vib_str} g and stator temperature is {temp_str} °C. "
            f"The AI fusion system has assessed this as a Warning state. "
            f"Schedule a maintenance inspection and increase monitoring frequency to every hour."
        )
    if alert_level == "CRITICAL":
        return (
            f"Critical fault condition detected. Vibration RMS of {vib_str} g and stator temperature of {temp_str} °C "
            f"are both outside safe operating limits. "
            f"Stop the motor immediately, implement lockout/tagout, and notify the site engineer before any restart."
        )
    return "Insufficient sensor data to produce a reliable assessment. Verify system connection and sensor operation."


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

    fault_type_name = prediction_result.get("fault_type_name", "Healthy")
    explanation     = prediction_result.get("explanation", "")
    fault_code      = prediction_result.get("fault_code", 0)
    fault_flags     = prediction_result.get("fault_flags", 0)
    thermal_status  = prediction_result.get("thermal_status", 0)
    faults          = prediction_result.get("faults", [])
    fault_count     = prediction_result.get("fault_count", len(faults))

    return {
        "type": "dashboard_update",
        "client_id": client_id,
        "machine_id": machine_id,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction_value,
        "alert_level": alert_level,
        "fault_code": fault_code,
        "fault_flags": fault_flags,
        "fault_type_name": fault_type_name,
        "explanation": explanation,
        "faults": faults,
        "fault_count": fault_count,
        "status": prediction_result.get("status", "unknown"),
        "model_used": model_used,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "inference_time_ms": _coerce_float(prediction_result.get("inference_time_ms")),
        "machine": {
            "machineId": machine_id,
            "healthState": alert_level,
            "faultCode": fault_code,
            "faultTypeName": fault_type_name,
            "faults": faults,
            "rulHours": rul_hours,
            "predictionCertainty": round(confidence, 4),
            "uncertainty": round(uncertainty, 4),
        },
        "sensors": {
            "phaseCurrent": sensor_summary["phaseCurrent"],
            "vibration": sensor_summary["vibration"],
            "temperature": sensor_summary["temperature"],
            "thermal": {**sensor_summary["thermal"], "status": thermal_status},
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
        """Attempt to load the trained Meta Fusion model and its paired StandardScaler."""
        import joblib
        # Load XGBoost StackingClassifier
        try:
            if _os.path.exists(_META_MODEL_PATH):
                self.meta_model = joblib.load(_META_MODEL_PATH)
                logger.info("✓ Meta Fusion XGBoost loaded from %s", _META_MODEL_PATH)
            else:
                logger.warning("Meta Fusion model not found at %s — using rule-based fallback.", _META_MODEL_PATH)
        except Exception as e:
            logger.warning("Failed to load Meta Fusion model: %s — using rule-based fallback.", e)
            self.meta_model = None

        # Load StandardScaler (fitted during training — required for MLP base estimator)
        self.meta_scaler = None
        try:
            if _os.path.exists(_META_SCALER_PATH):
                self.meta_scaler = joblib.load(_META_SCALER_PATH)
                logger.info("✓ Meta Fusion scaler loaded from %s", _META_SCALER_PATH)
            else:
                logger.warning("Meta Fusion scaler not found at %s — predictions will be unscaled.", _META_SCALER_PATH)
        except Exception as e:
            logger.warning("Failed to load Meta Fusion scaler: %s", e)
    
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
                        # Use the same smooth parabolic encoding as the training pipeline
                        # (build_nasa_probs from src/features/meta_fusion_features.py).
                        # The hard step-function previously here pushed p[WARNING]=0.80 for
                        # all mid-range RUL values, causing persistent WARNING misclassification.
                        if _META_FEATURES_AVAILABLE:
                            p_n = build_nasa_probs(np.array([rul]))[0]
                        else:
                            norm = float(np.clip(rul / 100.0, 0.0, 1.0))
                            p_n = np.array([norm, 4.0*norm*(1.0-norm), 1.0-norm], dtype=np.float32)
                            p_n = p_n / (p_n.sum() + 1e-9)
                        
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
                    # Simulink sends a 3×3 matrix (list of lists); legacy path sends base64 str
                    if isinstance(thermal_img, list):
                        res_t = thermal_service.predict_from_matrix(thermal_img)
                    else:
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
                # Auto-detect Kelvin vs Celsius: Simscape outputs Kelvin (values ≥ 274 K for
                # any real operating motor). If the Simulink port is connected to a workspace
                # _C variable (e.g. T_stator_C = 135) instead of the _K variable (408.15),
                # the raw value is < 273 and is already in °C — no conversion needed.
                # Threshold: > 273 → Kelvin (subtract 273.15); ≤ 273 → already Celsius.
                _to_celsius = _auto_celsius  # module-level auto-detect K vs °C

                # Initialise with defaults — will be overwritten from scalars or thermal image
                motor_temp: float = 0.0
                amb_temp:   float = 25.0
                _got_temp = False

                if scalars and len(scalars) >= 4:
                    motor_temp = _to_celsius(float(scalars[2]))
                    amb_temp   = _to_celsius(float(scalars[3]))
                    _got_temp  = True

                # Thermal frame — FALLBACK ONLY.
                #
                # This previously did `if not _got_temp or _T_max > motor_temp`,
                # i.e. the hottest cell of the infrared frame silently replaced a
                # perfectly valid stator reading from scalars[2]. That is wrong on
                # two counts: the frame images the housing/hotspots, not the stator
                # winding, and the IEC 60034-1 comparison below is defined on the
                # WINDING temperature. A housing hotspot ≥ 95 °C would push ΔT past
                # 70 K and escalate a genuine WARNING to CRITICAL.
                #
                # The frame is now used only when scalars gave us nothing. A hotspot
                # hotter than the winding still raises the thermal alarm, but through
                # _hotspot_temp below — it never masquerades as the winding value.
                _hotspot_temp: Optional[float] = None
                _ti_check = sensor_data.get('thermal_image')
                if _ti_check is not None:
                    try:
                        _T_mat = np.array(_ti_check, dtype=np.float32).flatten()
                        _hotspot_temp = _to_celsius(float(np.max(_T_mat)))
                        if not _got_temp:
                            motor_temp = _hotspot_temp
                            _got_temp  = True
                            logger.debug("Winding temperature taken from thermal frame "
                                         "(%.1f °C) — no scalar reading present", motor_temp)
                    except Exception:
                        pass

                if _got_temp:
                    p_s = np.array([1.0, 0.0, 0.0])   # Start Healthy
                    s_val = 0.0

                    # Thermal Thresholds — IEC 60034-1 Class F insulation
                    # Stator winding: warn > 95 °C, critical > 120 °C
                    # Temperature rise (ΔT): warn > 50 K, critical > 70 K
                    if motor_temp > 120 or (motor_temp - amb_temp) > 70:
                        p_s = np.array([0.0, 0.0, 1.0]); s_val = 0.95
                        logger.warning(
                            f"CRITICAL: High Motor Temp ({motor_temp:.1f} °C) — IEC 60034-1 Class F limit 155 °C")
                    elif motor_temp > 95 or (motor_temp - amb_temp) > 50:
                        p_s = np.array([0.0, 1.0, 0.0]); s_val = 0.5
                        logger.warning(f"WARNING: Elevated Motor Temp ({motor_temp:.1f} °C)")
                        
                    # Electrical Overload — sensor reads LINE current (delta): rated 129 A line / 74.5 A phase
                    if curr_data.size > 0:
                        rms_c = np.sqrt(np.mean(curr_data**2))
                        if rms_c > 148:  # >115% of rated line current (129 A) — CRITICAL overload
                            p_s = np.array([0.0, 0.0, 1.0]); s_val = 0.99
                            logger.error(f"CRITICAL: Current overload ({rms_c:.2f} A > 148 A — 115% of rated 129 A line)")
                        elif rms_c > 129:  # >100% rated line current — WARNING
                            if s_val < 0.5:
                                p_s = np.array([0.0, 1.0, 0.0]); s_val = 0.5
                            logger.warning(f"WARNING: Current above rated ({rms_c:.2f} A > 129 A rated line)")

                    predictions_list.append({
                        "val": s_val,
                        "unc": 0.0,
                        "model": "SCALAR_SAFETY_EXPERT",
                        "conf": 1.0,
                        "probs": p_s,
                        "id": "Scalar"
                    })
                        
                # ── Physics Gate: override CNN domain shift for clearly healthy signals ──
                # When physical measurements are all within healthy limits, CNN domain shift
                # (models trained on real test-rig data vs synthetic Simulink sinusoids) must
                # not cause a false fault alert.
                #
                # Three conditions — current excluded because Simulink startup transients
                # and delta-connection line vs phase current ambiguity make it unreliable:
                #   1. Vibration < 1.5 g  (ISO 10816-3 Group II Zone A/B boundary)
                #   2. Motor temp < 95 °C  (IEC 60034-1 Class F winding WARNING threshold)
                #      NOTE: threshold was 85°C but that is below the IEC warning limit and
                #      caused false trips when bearing friction raised housing temperature.
                #   3. ΔT = (motor_temp − ambient) < 40 K
                #      This discriminates NORMAL (ΔT≈25 K) from FAULT (ΔT≈53 K for 78°C
                #      stator) even if absolute temperature would pass condition 2 alone.
                if predictions_list:
                    _vib_rms_g = float(np.sqrt(np.mean(vib_data[:2048]**2))) if vib_data.size >= 2048 else 0.0
                    _curr_rms_g = float(np.sqrt(np.mean(curr_data**2))) if curr_data.size > 0 else 0.0
                    _delta_t_g = motor_temp - amb_temp
                    _physics_normal = (
                        _vib_rms_g  < 1.5    and   # ISO 10816-3: Zone A/B boundary
                        motor_temp  < 95.0   and   # IEC 60034-1 Class F winding warning = 95°C
                        _delta_t_g  < 40.0         # temperature RISE discriminates NORMAL (25K) from FAULT (53K)
                    )
                    if _physics_normal:
                        logger.info(
                            "Physics gate: all parameters healthy "
                            "(vib=%.3fg, temp=%.1f°C, ΔT=%.1fK, curr=%.1fA) — forcing NORMAL",
                            _vib_rms_g, motor_temp, _delta_t_g, _curr_rms_g
                        )
                        return {
                            "prediction":      0.0,
                            "alert_level":     "NORMAL",
                            "fault_code":      0,
                            "fault_flags":     0,
                            "fault_type_name": "Healthy",
                            "faults":          [],
                            "fault_count":     0,
                            "thermal_status":  0,
                            "explanation":     _generate_fault_explanation(
                                "NORMAL", "Healthy", _vib_rms_g, motor_temp, None, 0.95
                            ),
                            "model_used":      "Physics Gate",
                            "inference_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                            "confidence":      0.95,
                            "uncertainty":     0.05,
                            "rul_hours":       None,
                            "status":          "success",
                            "modalities":      predictions_list
                        }

                # ── 3. Fuse Expert Predictions ─────────────────────────────────
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

                mod_map        = {p["id"]: p["probs"] for p in predictions_list}
                training_experts = ["CWRU", "Induction", "NASA", "Current", "Thermal"]
                models_used    = ", ".join(p["model"] for p in predictions_list)

                # Count REAL CNN modalities — exclude Scalar (physics expert, not a CNN).
                # Meta-fusion needs ≥ 2 independent CNN signals to be reliable;
                # 1 CNN + Scalar still only has 1 learned-model data point.
                _cnn_count = sum(1 for p in predictions_list if p["id"] != "Scalar")

                # Build 32-dim feature vector matching training pipeline exactly.
                # Scalar is excluded here — it is a physics veto, not a trained signal.
                if _META_FEATURES_AVAILABLE:
                    preds_for_fusion = {
                        name: mod_map.get(name, np.ones(3) / 3.0).reshape(1, 3)
                        for name in training_experts
                    }
                    score_vec = extract_meta_features_from_predictions(preds_for_fusion)
                else:
                    # Manual 32-dim fallback — identical layout to meta_fusion_features.py
                    _f = []
                    _prob5 = [mod_map.get(n, np.ones(3) / 3.0) for n in training_experts]
                    for _p5 in _prob5:
                        _ent  = -np.sum(_p5 * np.log(np.clip(_p5, 1e-7, 1.0)))
                        _sp   = np.sort(_p5)
                        _marg = float(_sp[-1] - _sp[-2])
                        _f.extend([*_p5, _ent, _marg])   # 5 dims × 5 experts = 25
                    _mean5 = np.mean(_prob5, axis=0)
                    _var5  = np.var(_prob5,  axis=0)
                    _f.extend(_mean5)                     # + 3
                    _f.extend(_var5)                      # + 3
                    _f.append(-np.sum(_mean5 * np.log(np.clip(_mean5, 1e-7, 1.0))))  # + 1 = 32
                    score_vec = np.array(_f, dtype=np.float32).reshape(1, -1)

                # ── Primary decision: Meta Fusion XGBoost ────────────────────────
                class_idx   = 0
                alert       = "NORMAL"
                confidence  = 1.0
                uncertainty = 0.0
                val         = 0.0
                fusion_mode = "Meta Fusion"

                if self.meta_model is not None and _cnn_count >= 2:
                    try:
                        scaled_vec  = (self.meta_scaler.transform(score_vec)
                                       if self.meta_scaler is not None else score_vec)
                        class_idx   = int(self.meta_model.predict(scaled_vec)[0])
                        _probs      = self.meta_model.predict_proba(scaled_vec)[0]
                        confidence  = float(_probs[class_idx])
                        alert       = ["NORMAL", "WARNING", "CRITICAL"][class_idx]
                        val         = float(class_idx) / 2.0
                        uncertainty = 1.0 - confidence
                    except Exception as _fuse_exc:
                        logger.warning("Meta fusion failed (%s) — switching to rule-based.", _fuse_exc)
                        fusion_mode = "Rule-Based (fallback)"
                else:
                    _reason = ("model not loaded" if self.meta_model is None
                               else f"only {_cnn_count} CNN modality available")
                    logger.info("Rule-based fusion (%s).", _reason)
                    fusion_mode = "Rule-Based (fallback)"

                if fusion_mode == "Rule-Based (fallback)":
                    # Confidence-weighted vote across CNN experts only (Scalar excluded).
                    # Weighted voting is more robust than worst-case for NORMAL conditions
                    # where one confused CNN should not override four healthy ones.
                    _cnn_preds = [p for p in predictions_list if p["id"] != "Scalar"]
                    if _cnn_preds:
                        _tw   = sum(p["conf"] for p in _cnn_preds) + 1e-9
                        _agg  = np.zeros(3, dtype=np.float32)
                        for _p in _cnn_preds:
                            _agg += float(_p["conf"]) * np.array(_p["probs"], dtype=np.float32)
                        _agg  /= _tw
                        class_idx   = int(np.argmax(_agg))
                        confidence  = float(_agg[class_idx])
                        alert       = ["NORMAL", "WARNING", "CRITICAL"][class_idx]
                        val         = float(class_idx) / 2.0
                        uncertainty = 1.0 - confidence
                    else:
                        # No CNN modalities at all — cannot decide; leave as UNKNOWN
                        alert = "UNKNOWN"; confidence = 0.0; uncertainty = 1.0; val = 0.0

                # ── Scalar Safety Expert: Bidirectional Override ──────────────────
                # MUST run unconditionally — after BOTH meta-fusion AND rule-based.
                # Previous bug: this block was inside the meta-fusion branch only,
                # so when the meta-model was missing or threw an exception the Scalar
                # override silently never ran, causing NORMAL conditions to return WARNING.
                #
                # IEC 60034-1 Class F temperature thresholds are deterministic physics
                # laws — they cannot be overridden by any stochastic learned signal.
                scalar_pred = mod_map.get("Scalar")
                if scalar_pred is not None:
                    scalar_class = int(np.argmax(scalar_pred))

                    if scalar_class > class_idx:
                        # UPGRADE: breach of IEC 60034-1 thermal limits detected
                        _prev = alert
                        class_idx   = scalar_class
                        alert       = ["NORMAL", "WARNING", "CRITICAL"][class_idx]
                        confidence  = float(scalar_pred[class_idx])
                        uncertainty = 1.0 - confidence
                        val         = float(class_idx) / 2.0
                        logger.warning(
                            "Scalar upgraded %s → %s (IEC 60034-1 temperature threshold)", _prev, alert)

                    elif scalar_class == 1 and class_idx == 2:
                        # CEILING: IEC physics says at most WARNING (temp 95–120 °C / ΔT 50–70 K).
                        #
                        # CRITICAL is defined by IEC 60034-1: temp > 120 °C OR ΔT > 70 K.
                        # If scalar says WARNING, neither threshold has been crossed.  A
                        # CRITICAL prediction from a CNN is therefore physically impossible
                        # and must be overridden — IEC thermal laws are deterministic.
                        #
                        # Exception: if vibration is in ISO 10816-3 Zone C/D (> 2.04 g), a
                        # mechanical CRITICAL can coexist with only WARNING-level temperatures
                        # (e.g. bearing seize milliseconds before thermal runaway).  In that
                        # case respect the CNN and do NOT cap.
                        _vib_for_ceil = (
                            float(np.sqrt(np.mean(vib_data[:2048]**2)))
                            if vib_data.size >= 2048 else 0.0
                        )
                        _vib_critical = _vib_for_ceil > 2.04   # ISO Zone C/D boundary (g)
                        if not _vib_critical:
                            _prev       = alert
                            class_idx   = 1
                            alert       = "WARNING"
                            confidence  = float(scalar_pred[1])
                            uncertainty = 1.0 - confidence
                            val         = 0.5
                            logger.warning(
                                "Scalar ceiling: capped CRITICAL → WARNING "
                                "(scalar=WARNING, vib=%.3fg < 2.04g ISO Zone C — "
                                "IEC temps have not reached CRITICAL threshold)", _vib_for_ceil)

                    elif scalar_class == 0 and class_idx > 0:
                        # DOWNGRADE consideration: ALL temperatures are clearly healthy.
                        # CNN models have domain shift on Simulink synthetic signals
                        # (trained on real test-rig data, not synthesised sinusoids);
                        # they predict bearing faults even with A_impact=0. Trust the
                        # physics when three independent evidences point to healthy state:
                        #   (a) meta-fusion / rule-based is NOT highly confident (< 0.90)
                        #   (b) no individual CNN expert is strongly detecting a fault (< 0.85)
                        #   (c) NASA Bi-LSTM RUL corroborates healthy state (RUL > 50 h)
                        _nasa_rul = None
                        for _p in predictions_list:
                            if _p["id"] == "NASA":
                                _nasa_rul = float(_p["val"]) * 100.0
                                break

                        _max_fault_c = max(
                            (float(np.max(np.array(mod_map[n], dtype=np.float32)[1:]))
                             for n in training_experts if n in mod_map),
                            default=0.0
                        )
                        _nasa_ok  = (_nasa_rul is None) or (_nasa_rul > 50.0)
                        _conf_ok  = confidence < 0.92   # was 0.90 — relaxed for domain-shifted signals
                        _fault_ok = _max_fault_c < 0.90  # was 0.85 — relaxed for synthetic Simulink waveforms

                        if _conf_ok and _fault_ok and _nasa_ok:
                            _prev       = ["NORMAL", "WARNING", "CRITICAL"][class_idx]
                            class_idx   = 0
                            alert       = "NORMAL"
                            confidence  = float(scalar_pred[0])
                            uncertainty = 1.0 - confidence
                            val         = 0.0
                            logger.info(
                                "Scalar downgraded %s → NORMAL "
                                "(fusion_conf=%.2f, max_cnn_fault=%.2f, nasa_rul=%s, all temps healthy)",
                                _prev, confidence, _max_fault_c,
                                f"{_nasa_rul:.1f}h" if _nasa_rul is not None else "n/a"
                            )

                # ── RUL hours ─────────────────────────────────────────────────────
                # Use real NASA Bi-LSTM output when available; otherwise estimate
                # from health class (NORMAL ≈ 20 000 h remaining, CRITICAL ≈ 0 h).
                rul_hours_out: Optional[float] = None
                for _p in predictions_list:
                    if _p["id"] == "NASA":
                        rul_hours_out = round(float(_p["val"]) * 100.0, 2)
                        break
                if rul_hours_out is None:
                    rul_hours_out = round(max(0.0, (1.0 - float(val)) * 20000.0), 2)

                # ── Thermal status ────────────────────────────────────────────────
                # Independent of fault_flags — thermal alarm can coexist with any
                # mechanical fault. 0=OK, 1=Thermal WARNING, 2=Thermal CRITICAL.
                thermal_status = 0
                for _p in predictions_list:
                    if _p["id"] == "Thermal":
                        if _p["val"] > 0.6:   thermal_status = 2
                        elif _p["val"] > 0.3: thermal_status = 1
                        break
                # A surface hotspot hotter than the winding is a real thermal
                # finding and still raises the alarm here — it just no longer
                # overwrites the winding temperature used for the IEC comparison.
                if _hotspot_temp is not None and _hotspot_temp > motor_temp:
                    if _hotspot_temp > 120:
                        thermal_status = max(thermal_status, 2)
                    elif _hotspot_temp > 95:
                        thermal_status = max(thermal_status, 1)
                if scalars and len(scalars) >= 4:
                    _mt = _to_celsius(float(scalars[2]))
                    _at = _to_celsius(float(scalars[3]))
                    if _mt > 120 or (_mt - _at) > 70:
                        thermal_status = max(thermal_status, 2)
                    elif _mt > 95 or (_mt - _at) > 50:
                        thermal_status = max(thermal_status, 1)

                # ── Multi-fault detection: bitmask ────────────────────────────────
                # A motor can have simultaneous faults (e.g. bearing wear AND
                # overheating). fault_flags encodes all active faults as a bitmask
                # so MATLAB can check each fault type independently:
                #   bit 0  (1) = Bearing fault       — CWRU/Current CNN
                #   bit 1  (2) = Rotor misalignment  — Current/Induction CNN
                #   bit 2  (4) = Shaft fault          — Induction CNN Ring class
                #   bit 3  (8) = Thermal fault        — Thermal CNN / Scalar IEC alarm
                # Example: fault_flags=9 means Bearing(1) + Thermal(8) simultaneously.
                # MATLAB check: bitand(Fault_Type, 1)>0  → bearing fault present
                _F_BEAR  = F_BEARING
                _F_ROTOR = F_ROTOR
                _F_STAT  = F_STATOR
                _F_THER  = F_THERMAL

                fault_flags = 0
                _evidence: Dict[int, list] = {}

                def _mark(bit: int, source: str):
                    nonlocal fault_flags
                    fault_flags |= bit
                    _evidence.setdefault(bit, []).append(source)

                if alert not in ("NORMAL", "UNKNOWN"):
                    def _find(mid):
                        return next((p for p in predictions_list if p["id"] == mid), None)

                    _cw = _find("CWRU");      _cu = _find("Current")
                    _in = _find("Induction"); _th = _find("Thermal")

                    # CWRU-CNN is a 4-class model truncated to 3 health slots. On
                    # Simulink-synthesised signals it collapses onto the dropped 4th
                    # class, leaving probs ≈ [0,0,0] — a degenerate output that must
                    # not be read as bearing evidence, or every fault state would be
                    # labelled "bearing" regardless of the actual signal.
                    _cw_usable = False
                    if _cw is not None:
                        _cw_mass = float(np.sum(np.asarray(_cw.get("probs", []), dtype=np.float64)[:3]))
                        _cw_usable = _cw_mass > 0.10

                    # ── Bearing: CWRU race classes, Current-CNN, Induction D1 ──
                    if _cw_usable and any(k in _cw.get("model", "") for k in ("Inner", "Ball", "Outer")) \
                            and _cw["conf"] > 0.45:
                        _mark(_F_BEAR, "CWRU-CNN bearing race class")
                    if _cu and "Bearing-Fault" in _cu.get("model", "") and _cu["conf"] > 0.45:
                        _mark(_F_BEAR, "Current-CNN bearing signature")
                    if _in and "D1" in _in.get("model", "") and _in["conf"] > 0.45:
                        _mark(_F_BEAR, "Induction-CNN class D1 (bearing)")

                    # ── Rotor cage: broken bar (Current) or end-ring (Induction Ring) ──
                    if _cu and "Broken-Rotor-Bar" in _cu.get("model", "") and _cu["conf"] > 0.45:
                        _mark(_F_ROTOR, "Current-CNN broken-rotor-bar signature")
                    if _in and "Ring" in _in.get("model", "") and _in["conf"] > 0.45:
                        _mark(_F_ROTOR, "Induction-CNN class Ring (rotor end-ring)")

                    # ── Stator winding: Induction D2 ──
                    if _in and "D2" in _in.get("model", "") and _in["conf"] > 0.45:
                        _mark(_F_STAT, "Induction-CNN class D2 (stator)")

                    # ── Thermal: IEC 60034-1 scalar alarm or Thermal-CNN ──
                    if thermal_status >= 2:
                        _mark(_F_THER, "IEC 60034-1 winding limit exceeded")
                    elif thermal_status >= 1:
                        _mark(_F_THER, "IEC 60034-1 winding warning threshold")

                    # No expert identified a specific type — report the generic
                    # condition rather than inventing a bearing fault.
                    if fault_flags == 0:
                        _mark(_F_BEAR, "fusion score elevated (unspecified modality)")

                # Primary fault code (highest-priority active fault, backward compat)
                if   fault_flags & _F_THER:  fault_code = 4
                elif fault_flags & _F_STAT:  fault_code = 3
                elif fault_flags & _F_ROTOR: fault_code = 2
                elif fault_flags & _F_BEAR:  fault_code = 1
                else:                        fault_code = 0

                # vib_data is already in g (api_wrapper converted m/s² → g before sending)
                _vib_rms_for_expl = float(np.sqrt(np.mean(vib_data[:2048]**2))) if vib_data.size >= 2048 else 0.0

                # Expand the bitmask into a named, explained fault list.
                _fault_list = _build_fault_list(
                    fault_flags, _evidence, motor_temp, _vib_rms_for_expl)
                _active_bits = len(_fault_list)
                # fault_code 5 == "two or more active" is the MATLAB contract and is
                # preserved; the human-readable name now lists the faults instead.
                _eff_fault_code  = 5 if _active_bits > 1 else fault_code
                _fault_type_name = _compose_fault_name(_fault_list)

                _explanation = _generate_fault_explanation(
                    alert, _fault_type_name, _vib_rms_for_expl, motor_temp,
                    rul_hours_out, round(confidence, 4), faults=_fault_list
                )

                return {
                    "prediction":      round(float(val), 4),
                    "alert_level":     alert,
                    "fault_code":      _eff_fault_code,
                    "fault_flags":     int(fault_flags),
                    "fault_type_name": _fault_type_name,
                    # Every active fault, named and explained individually, so the
                    # frontend can list them instead of showing "Multiple Faults".
                    "faults":          _fault_list,
                    "fault_count":     _active_bits,
                    "thermal_status":  thermal_status,
                    "explanation":     _explanation,
                    "model_used":      f"[{fusion_mode}] {models_used}",
                    "inference_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "confidence":      round(confidence, 4),
                    "uncertainty":     round(uncertainty, 4),
                    "rul_hours":       rul_hours_out,
                    "status":          "success",
                    "modalities":      predictions_list
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
                    model_used = f"Current-CNN ({['Healthy', 'Bearing-Fault', 'Broken-Rotor-Bar'][min(idx, 2)]})"
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
        "fault_code":         result.get("fault_code", 0),        # 0=None 1=Bearing 2=Rotor 3=Stator 4=Thermal 5=Multiple
        "fault_flags":        result.get("fault_flags", 0),       # bitmask: bit0=Bearing bit1=Rotor bit2=Stator bit3=Thermal
        # Human-readable name and per-fault breakdown. Previously omitted, so the
        # MATLAB HTTP fallback and any REST consumer never received them.
        "fault_type_name":    result.get("fault_type_name", "Healthy"),
        "faults":             result.get("faults", []),
        "fault_count":        result.get("fault_count", 0),
        "explanation":        result.get("explanation", ""),
        "thermal_status":     result.get("thermal_status", 0),    # 0=OK 1=WARNING 2=CRITICAL
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
                    "fault_code":     prediction_result.get("fault_code", 0),    # 0=None 1=Bearing 2=Rotor 3=Shaft 4=Thermal
                    "fault_flags":    prediction_result.get("fault_flags", 0),   # bitmask: bit0=Bearing bit1=Rotor bit2=Shaft bit3=Thermal
                    "thermal_status": prediction_result.get("thermal_status", 0),# 0=OK 1=WARNING 2=CRITICAL
                    "model_used": prediction_result["model_used"],
                    "confidence": prediction_result["confidence"],
                    "uncertainty": prediction_result.get("uncertainty", 0.0),
                    "rul_hours": prediction_result.get("rul_hours"),              # None = not determined; 0 = imminent failure
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
    try:
        await websocket.send_json({
            "type": "connection_confirmed",
            "message": "Dashboard stream connected",
            "timestamp": datetime.now().isoformat(),
            "backend_state": "healthy",
            "active_clients": manager.get_connection_count()
        })
        # Heartbeat loop: sleep 30 s then send a ping to confirm the connection
        # is still alive. Using asyncio.sleep (not wait_for + receive_text) to
        # avoid the Python 3.12 asyncio bug where wait_for cancellation leaves
        # the WebSocket receive buffer in an invalid state and raises RuntimeError
        # on the next call — which was causing the frontend to see constant disconnects.
        while True:
            await asyncio.sleep(30.0)
            await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
    except (WebSocketDisconnect, RuntimeError, ConnectionResetError, Exception):
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

