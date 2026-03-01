from pydantic import BaseModel, Field
from typing import Optional


class RegionResponse(BaseModel):
    region_id: str
    name: str
    lat: float
    lng: float
    primary_crop: str
    stress_score: Optional[float] = None

    model_config = {"from_attributes": True}


class ClimateResponse(BaseModel):
    temperature_anomaly: float
    drought_index: float = Field(ge=0, le=100)
    rainfall_anomaly: float
    ndvi_score: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)
    yield_stress_score: Optional[float] = None

    model_config = {"from_attributes": True}


class StressResponse(BaseModel):
    yield_stress_score: float = Field(ge=0, le=100)
    breakdown: dict

    model_config = {"from_attributes": True}


class FinancialResponse(BaseModel):
    interest_rate: float
    probability_of_default: float
    insurance_premium: float
    repayment_flexibility: float
    baseline_rate: float
    rate_floor: float = 0.0
    rate_ceiling: float = 0.0
    repayment_months: int = 36
    delta_from_baseline: float = 0.0

    model_config = {"from_attributes": True}


class ComparisonResponse(BaseModel):
    old_system: dict
    terralend: dict


class SystemDetails(BaseModel):
    region_id: str
    climate: ClimateResponse
    stress: StressResponse
    financial: FinancialResponse


class SimulateRequest(BaseModel):
    region_id: str
    temperature_delta: Optional[float] = None
    drought_index: Optional[float] = None
    rainfall_anomaly: Optional[float] = None
    ndvi_score: Optional[float] = None
    soil_moisture: Optional[float] = None


class SimulateResponse(BaseModel):
    region_id: str
    baseline: FinancialResponse
    simulated: FinancialResponse
    stress_score: float
    baseline_stress: float
    deltas: dict
