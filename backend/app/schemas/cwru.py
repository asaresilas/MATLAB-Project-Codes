from pydantic import BaseModel, Field
from typing import List

class CWRUInput(BaseModel):
    # CWRU models expect a raw vibration signal segment.
    # Shape: (1000, 1) -> 1000 time steps.
    signal: List[float] = Field(..., description="Raw vibration signal segment. Length: 1000")

class CWRUPrediction(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict
