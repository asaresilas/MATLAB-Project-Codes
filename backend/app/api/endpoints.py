"""
REST prediction endpoints.

All /predict/* routes require a valid X-API-Key header (via verify_api_key).
Model inference is wrapped in asyncio.to_thread() so Keras forward passes
never block the async event loop.
"""

import asyncio
import logging

import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from app.auth.api_key import verify_api_key
from app.services.model_registry import registry
from app.services.thermal_service import thermal_service
from app.schemas.cia1 import CIA1Input, CIA1Prediction
from app.schemas.nasa import NASAInput, NASAPrediction
from app.schemas.cwru import CWRUInput, CWRUPrediction
from app.schemas.induction import InductionInput, InductionPrediction
from app.schemas.current import CurrentInput, CurrentPrediction
from app.schemas.thermal import ThermalInput, ThermalPrediction
from src.features.signal_processing import extract_nasa_features

logger = logging.getLogger(__name__)

router = APIRouter(tags=["prediction"])

# ── Shorthand: run a sync callable off the event loop ─────────────────────────
async def _infer(fn, *args, **kwargs):
    """Run a blocking callable in a thread pool so it doesn't block the loop."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ── Model listing (public — no auth needed) ────────────────────────────────────

@router.get("/models", summary="List loaded models and their status")
async def list_models():
    """Returns the names and descriptions of all currently loaded models.
    File-system paths are intentionally omitted from the response."""
    return {
        "models_loaded": len(registry.models),
        "models": {
            name: {
                "description": cfg.get("description", ""),
                "has_scaler":  name in registry.scalers,
                "loaded":      True,
            }
            for name, cfg in registry.configs.items()
        },
    }


# ── CIA-1 ──────────────────────────────────────────────────────────────────────

@router.post("/predict/cia1", response_model=CIA1Prediction,
             summary="CIA-1 MLP failure-mode prediction")
async def predict_cia1(
    input_data: CIA1Input,
    _user: dict = Depends(verify_api_key),
):
    model = registry.get_model("CIA1")
    if not model:
        raise HTTPException(status_code=503, detail="CIA1 model not loaded")

    # One-hot encode Type (H=100, L=010, M=001 — pandas get_dummies alphabetical)
    type_map = {"H": [1, 0, 0], "L": [0, 1, 0], "M": [0, 0, 1]}
    if input_data.type not in type_map:
        raise HTTPException(status_code=422, detail="'type' must be 'L', 'M', or 'H'")

    features = [
        input_data.air_temperature,
        input_data.process_temperature,
        input_data.rotational_speed,
        input_data.torque,
        input_data.tool_wear,
        *type_map[input_data.type],
    ]
    input_array = np.array([features], dtype=np.float32)

    try:
        prediction = await _infer(model.predict, input_array, verbose=0)
        class_names = ["No Failure", "Tool Wear Failure", "Overstrain Failure", "Power Failure"]
        idx = int(np.argmax(prediction[0]))
        return CIA1Prediction(
            predicted_class=class_names[idx],
            confidence=float(prediction[0][idx]),
            probabilities={n: float(p) for n, p in zip(class_names, prediction[0])},
        )
    except Exception as exc:
        logger.error("CIA1 inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# ── NASA RUL ───────────────────────────────────────────────────────────────────

@router.post("/predict/nasa", response_model=NASAPrediction,
             summary="NASA Bi-LSTM RUL prediction (hours)")
async def predict_nasa(
    input_data: NASAInput,
    _user: dict = Depends(verify_api_key),
):
    model = registry.get_model("NASA")
    scaler = registry.get_scaler("NASA")
    if not model:
        raise HTTPException(status_code=503, detail="NASA model not loaded")

    try:
        if input_data.signal:
            if not scaler:
                raise HTTPException(status_code=503, detail="NASA scaler not loaded")
            feats = extract_nasa_features(np.array(input_data.signal))
            feat_vec = np.array([
                feats["rms"], feats["mean"], feats["std"], feats["max"], feats["min"],
                feats["kurtosis"], feats["skewness"], feats["peak_to_peak"], feats["crest_factor"],
            ] * 4).reshape(1, -1)
            scaled = await _infer(scaler.transform, feat_vec)
            input_array = np.repeat(scaled, 30, axis=0).reshape(1, 30, 36).astype(np.float32)

        elif input_data.data:
            arr = np.array(input_data.data)
            if arr.shape == (36,):
                arr = np.repeat(arr.reshape(1, 36), 30, axis=0)
            elif arr.shape[0] < 30:
                arr = np.pad(arr, ((0, 30 - arr.shape[0]), (0, 0)), mode="edge")
            elif arr.shape[0] > 30:
                arr = arr[-30:]
            input_array = arr.reshape(1, 30, 36).astype(np.float32)

        else:
            raise HTTPException(status_code=422, detail="Provide 'signal' or 'data'.")

        prediction = await _infer(model.predict, input_array, verbose=0)
        return NASAPrediction(rul=float(prediction[0][0]))

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("NASA inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# ── CWRU Bearing ───────────────────────────────────────────────────────────────

@router.post("/predict/cwru", response_model=CWRUPrediction,
             summary="CWRU-CNN bearing fault classification")
async def predict_cwru(
    input_data: CWRUInput,
    _user: dict = Depends(verify_api_key),
):
    model = registry.get_model("CWRU")
    if not model:
        raise HTTPException(status_code=503, detail="CWRU model not loaded")

    input_array = np.array(input_data.signal, dtype=np.float32).reshape(1, 1000, 1)
    try:
        prediction = await _infer(model.predict, input_array, verbose=0)
        class_names = ["Normal", "Inner Race", "Ball", "Outer Race"]
        idx = int(np.argmax(prediction[0]))
        return CWRUPrediction(
            predicted_class=class_names[idx],
            confidence=float(prediction[0][idx]),
            probabilities={n: float(p) for n, p in zip(class_names, prediction[0])},
        )
    except Exception as exc:
        logger.error("CWRU inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# ── Induction Motor ────────────────────────────────────────────────────────────

@router.post("/predict/induction", response_model=InductionPrediction,
             summary="Induction motor health classification (2048-point signal)")
async def predict_induction(
    input_data: InductionInput,
    _user: dict = Depends(verify_api_key),
):
    model = registry.get_model("Induction_Motor")
    if not model:
        raise HTTPException(status_code=503, detail="Induction Motor model not loaded")

    input_array = np.array(input_data.signal, dtype=np.float32).reshape(1, 2048, 1)
    try:
        prediction = await _infer(model.predict, input_array, verbose=0)
        class_names = ["Healthy", "Damaged 1", "Damaged 2", "Damaged Ring"]
        idx = int(np.argmax(prediction[0]))
        return InductionPrediction(
            predicted_class=class_names[idx],
            confidence=float(prediction[0][idx]),
            probabilities={n: float(p) for n, p in zip(class_names, prediction[0])},
        )
    except Exception as exc:
        logger.error("Induction inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# ── 3-Phase Current Signature ──────────────────────────────────────────────────

@router.post("/predict/current", response_model=CurrentPrediction,
             summary="3-phase current signature fault classification")
async def predict_current(
    input_data: CurrentInput,
    _user: dict = Depends(verify_api_key),
):
    model = registry.get_model("Current_Signature")
    if not model:
        raise HTTPException(status_code=503, detail="Current Signature model not loaded")

    raw = np.array(input_data.data, dtype=np.float32)
    peak = np.max(np.abs(raw))
    normalized = raw / peak if peak > 1e-9 else raw
    input_array = normalized.reshape(1, 1000, 3)

    try:
        prediction = await _infer(model.predict, input_array, verbose=0)
        class_names = ["Healthy", "Stator Fault", "Rotor Fault"]
        idx = int(np.argmax(prediction[0]))
        return CurrentPrediction(
            predicted_class=class_names[idx],
            confidence=float(prediction[0][idx]),
            probabilities={n: float(p) for n, p in zip(class_names, prediction[0])},
        )
    except Exception as exc:
        logger.error("Current Signature inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")


# ── Thermal Imaging ────────────────────────────────────────────────────────────

@router.post("/predict/thermal", response_model=ThermalPrediction,
             summary="Thermal image fault classification (MobileNetV2)")
async def predict_thermal(
    input_data: ThermalInput,
    _user: dict = Depends(verify_api_key),
):
    try:
        result = await _infer(thermal_service.process_and_predict, input_data.image_base64)
    except Exception as exc:
        logger.error("Thermal inference error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Return only fields defined in ThermalPrediction — extras are silently dropped.
    return ThermalPrediction(**result)
