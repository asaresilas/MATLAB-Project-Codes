"""
Comprehensive Diagnostic Endpoint

This endpoint combines multiple models to provide:
1. RUL (Remaining Useful Life) - WHEN failure will occur
2. Fault Classification - WHAT type of fault
3. Fault Localization - WHERE the problem is located
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import numpy as np
import logging
from app.services.model_registry import registry
from src.features.signal_processing import extract_nasa_features
from src.interface import model_manager

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

class ComprehensiveDiagnosticInput(BaseModel):
    """Input for comprehensive diagnostic analysis"""
    vibration_signal: List[float] = Field(..., description="Vibration sensor data")
    current_signal: Optional[List[List[float]]] = Field(None, description="3-phase current data (optional)")
    temperature: float = Field(..., description="Temperature in Celsius")
    speed: float = Field(..., description="Rotational speed in RPM")
    process_params: Optional[Dict] = Field(None, description="Process parameters for CIA1 (optional)")

class FaultLocation(BaseModel):
    """Detailed fault location information"""
    component: str = Field(..., description="Component name (e.g., 'Bearing', 'Stator', 'Rotor')")
    fault_type: str = Field(..., description="Specific fault type")
    confidence: float = Field(..., description="Confidence level 0-1")
    severity: str = Field(..., description="Severity: Low, Medium, High, Critical")

class ComprehensiveDiagnosticResult(BaseModel):
    """Complete diagnostic result"""
    # RUL Prediction
    rul_hours: float = Field(..., description="Remaining Useful Life in hours")
    rul_confidence: float = Field(..., description="RUL prediction confidence")
    rul_uncertainty: float = Field(0.0, description="RUL prediction uncertainty (std dev)")
    
    # Fault Localization
    fault_locations: List[FaultLocation] = Field(..., description="Detected faults with locations")
    
    # Overall Assessment
    overall_health: str = Field(..., description="Overall health: Healthy, Warning, Critical")
    priority_action: str = Field(..., description="Recommended action")
    
    # Detailed Analysis
    bearing_analysis: Optional[Dict] = Field(None, description="Bearing-specific analysis")
    motor_analysis: Optional[Dict] = Field(None, description="Motor-specific analysis")
    electrical_analysis: Optional[Dict] = Field(None, description="Electrical system analysis")

@router.post("/diagnose/comprehensive", response_model=ComprehensiveDiagnosticResult)
async def comprehensive_diagnosis(input_data: ComprehensiveDiagnosticInput):
    """
    Comprehensive diagnostic analysis combining all models.
    
    Returns:
    - RUL prediction (WHEN failure will occur)
    - Fault classification (WHAT is wrong)
    - Fault localization (WHERE the problem is)
    - Recommended actions
    """
    
    fault_locations = []
    bearing_analysis = {}
    motor_analysis = {}
    electrical_analysis = {}
    
    rul_hours = 0.0
    rul_confidence = 0.0
    rul_uncertainty = 0.0
    
    # 1. NASA RUL Prediction (WHEN)
    # Use ModelManager which implements TTA for confidence
    try:
        vibration_array = np.array(input_data.vibration_signal)
        rul_hours, rul_confidence = model_manager.predict_rul_dl(vibration_array, input_data.temperature)
    except Exception as e:
        logger.error(f"RUL Prediction failed: {e}")
        rul_hours = 0.0
        rul_confidence = 0.0

    
    # 2. CWRU Bearing Fault Classification (WHERE - Bearing)
    cwru_model = registry.get_model("CWRU")
    
    if cwru_model and len(input_data.vibration_signal) >= 1000:
        try:
            # Take first 1000 samples
            signal_1000 = np.array(input_data.vibration_signal[:1000]).reshape(1, 1000, 1)
            prediction = cwru_model.predict(signal_1000, verbose=0)
            
            class_names = ['Normal', 'Inner Race', 'Ball', 'Outer Race']
            predicted_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][predicted_idx])
            fault_type = class_names[predicted_idx]
            
            if fault_type != 'Normal':
                # Determine severity based on RUL
                if rul_hours and rul_hours < 50:
                    severity = "Critical"
                elif rul_hours and rul_hours < 100:
                    severity = "High"
                elif rul_hours and rul_hours < 200:
                    severity = "Medium"
                else:
                    severity = "Low"
                
                fault_locations.append(FaultLocation(
                    component="Bearing",
                    fault_type=fault_type,
                    confidence=confidence,
                    severity=severity
                ))
            
            bearing_analysis = {
                'fault_type': fault_type,
                'confidence': confidence,
                'probabilities': {
                    name: float(prob) 
                    for name, prob in zip(class_names, prediction[0])
                }
            }
            
        except Exception as e:
            logger.error(f"CWRU bearing analysis failed: {e}")
    
    # 3. Induction Motor Analysis (WHERE - Motor)
    induction_model = registry.get_model("Induction_Motor")
    
    if induction_model and len(input_data.vibration_signal) >= 2048:
        try:
            signal_2048 = np.array(input_data.vibration_signal[:2048]).reshape(1, 2048, 1)
            prediction = induction_model.predict(signal_2048, verbose=0)
            
            class_names = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']
            predicted_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][predicted_idx])
            motor_status = class_names[predicted_idx]
            
            if motor_status != 'Healthy':
                fault_locations.append(FaultLocation(
                    component="Motor",
                    fault_type=motor_status,
                    confidence=confidence,
                    severity="High" if "Ring" in motor_status else "Medium"
                ))
            
            motor_analysis = {
                'status': motor_status,
                'confidence': confidence,
                'probabilities': {
                    name: float(prob)
                    for name, prob in zip(class_names, prediction[0])
                }
            }
            
        except Exception as e:
            logger.error(f"Induction motor analysis failed: {e}")
    
    # 4. Current Signature Analysis (WHERE - Electrical)
    if input_data.current_signal:
        current_model = registry.get_model("Current_Signature")
        
        if current_model and len(input_data.current_signal) >= 1000:
            try:
                current_array = np.array(input_data.current_signal[:1000]).reshape(1, 1000, 3)
                prediction = current_model.predict(current_array, verbose=0)
                
                class_names = ['Healthy', 'Stator Fault', 'Rotor Fault']
                predicted_idx = np.argmax(prediction[0])
                confidence = float(prediction[0][predicted_idx])
                electrical_status = class_names[predicted_idx]
                
                if electrical_status != 'Healthy':
                    fault_locations.append(FaultLocation(
                        component="Electrical System",
                        fault_type=electrical_status,
                        confidence=confidence,
                        severity="High"
                    ))
                
                electrical_analysis = {
                    'status': electrical_status,
                    'confidence': confidence,
                    'probabilities': {
                        name: float(prob)
                        for name, prob in zip(class_names, prediction[0])
                    }
                }
                
            except Exception as e:
                logger.error(f"Current signature analysis failed: {e}")
    
    # 5. Overall Health Assessment
    if len(fault_locations) == 0:
        overall_health = "Healthy"
        priority_action = "Continue normal operation. Schedule routine maintenance."
    elif any(f.severity == "Critical" for f in fault_locations):
        overall_health = "Critical"
        priority_action = "IMMEDIATE ACTION REQUIRED: Stop operation and inspect equipment."
    elif any(f.severity == "High" for f in fault_locations):
        overall_health = "Warning"
        priority_action = "Schedule maintenance within 24-48 hours."
    else:
        overall_health = "Warning"
        priority_action = "Monitor closely. Schedule maintenance within 1 week."
    
    rul_hours = max(0, rul_hours)
    rul_confidence = float(rul_confidence)
    # Calculate uncertainty as a raw value if confidence is high-precision
    rul_uncertainty = (1.0 - rul_confidence) * (rul_hours if rul_hours > 0 else 100.0) / 10.0
    
    return ComprehensiveDiagnosticResult(
        rul_hours=rul_hours,
        rul_confidence=rul_confidence,
        rul_uncertainty=rul_uncertainty,
        fault_locations=fault_locations,
        overall_health=overall_health,
        priority_action=priority_action,
        bearing_analysis=bearing_analysis if bearing_analysis else None,
        motor_analysis=motor_analysis if motor_analysis else None,
        electrical_analysis=electrical_analysis if electrical_analysis else None
    )
