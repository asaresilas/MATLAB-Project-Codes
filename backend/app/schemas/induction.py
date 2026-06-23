from pydantic import BaseModel, Field
from typing import List

class InductionInput(BaseModel):
    # Induction Motor models expect a raw signal segment.
    # Shape: (2048, 1) -> 2048 time steps.
    signal: List[float] = Field(..., description="Raw signal segment. Length: 2048")

class InductionPrediction(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict
