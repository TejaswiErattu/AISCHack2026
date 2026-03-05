from pydantic import BaseModel


class ClimateSnapshot(BaseModel):
    temperature_anomaly_c: float   # e.g. +1.2 (deg C above normal)
    drought_index: float           # 0-100 (higher = worse)
    rainfall_anomaly_pct: float    # e.g. -22 (% below normal)
    ndvi_score: float              # 0-100 (higher = healthier)
    soil_moisture: float           # 0-100 (higher = wetter/better)
    source: str                    # "mock", "noaa+mock", etc.
    generated_at_epoch: int        # unix timestamp
