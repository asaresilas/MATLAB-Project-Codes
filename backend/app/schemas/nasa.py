from pydantic import BaseModel, Field
from typing import List

class NASAInput(BaseModel):
    # NASA models expect a sequence of data points.
    # Shape: (30, 36) -> 30 time steps, 36 features.
    # The user should send a list of 30 lists, each containing 36 floats.
    # OR send a raw signal (list of floats) and we extract features.
    data: List[List[float]] = Field(None, description="Sequence of sensor readings. Shape: (30, 36). Optional if signal is provided.")
    signal: List[float] = Field(None, description="Raw vibration signal. If provided, features will be extracted automatically.")

class NASAPrediction(BaseModel):
    rul: float = Field(..., description="Remaining Useful Life prediction")
