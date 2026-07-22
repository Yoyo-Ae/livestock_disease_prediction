from pydantic import BaseModel, Field
from typing import Literal, Optional

class PredictionInput(BaseModel):
    country: str = Field(...,example="Nigeria")
    disease_type : str = Field(
        ...,
        example ="Foot and Mouth disease",
        description = "One of: Foot and Mouth disease, Peste des petitis ruminants, "
                       "Lumpy skin disease. Contagious bovine pleuropneumonia, Rift Valley fever" 
    )
    species: str = Field(..., example="Cattle",
                         description= "One of: Cattle, Goats, Sheep, Small Ruminants, Poultry, Swine")
    year: int = Field(..., ge=2005, le=2030, example=2026)
    month: int = Field(..., ge=1, le=12, example=7)
    livestock_density: float = Field(..., ge=0, example=42.5)
    rainfall_mm: float = Field(..., ge=0, example=70.3)
    temp_celsuis: float = Field(..., example=30.5)
    rolling_outbreak_count: int = Field(..., ge=0, example=2)
    season: Literal["Wet", "Dry"]=Field(..., exmaple="Wet")
    source: Literal["react", "ussd"]=Field(default="react")

class PredictionOutput(BaseModel):
    predicted_class: int
    outbreak_probability: float
    risk_level: str
    message: str
    threshold_used: float
    model_name: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    threshold: float
    environment: str

class PredictionLogEntry(BaseModel):
    id: int
    timestamp: str
    source_interface: str
    predicted_class: int
    outbreak_probability: int
    risk_level: Optional[str]

