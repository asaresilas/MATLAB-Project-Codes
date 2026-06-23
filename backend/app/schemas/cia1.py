from pydantic import BaseModel, Field

class CIA1Input(BaseModel):
    """Input for the CIA-1 MLP failure-mode classifier (8 features after one-hot encoding of type)."""
    type: str                = Field(..., description="Machine type — must be 'L', 'M', or 'H'")
    air_temperature: float   = Field(..., description="Air temperature [K]")
    process_temperature: float = Field(..., description="Process temperature [K]")
    rotational_speed: float  = Field(..., description="Rotational speed [rpm]")
    torque: float            = Field(..., description="Torque [Nm]")
    tool_wear: float         = Field(..., description="Accumulated tool wear [min]")

class CIA1Prediction(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict
