from pydantic import BaseModel, Field
from typing import Dict, Optional

class ThermalInput(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded thermal image string")

class ThermalPrediction(BaseModel):
    predicted_class: str = Field(..., description="Predicted fault class")
    confidence: float = Field(..., description="Confidence score (0-1)")
    probabilities: Dict[str, float] = Field(..., description="Probability distribution for all classes")
