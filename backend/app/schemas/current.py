from pydantic import BaseModel, Field
from typing import List

class CurrentInput(BaseModel):
    # Current Signature models expect a sequence of 3-phase currents.
    # Shape: (1000, 3) -> 1000 time steps, 3 phases.
    data: List[List[float]] = Field(..., description="3-phase current signal. Shape: (1000, 3)")

class CurrentPrediction(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict
