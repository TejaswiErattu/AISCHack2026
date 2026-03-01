"""Mock climate data layer.

Provides deterministic, realistic climate data for all 20 US agricultural regions.
Used as the primary data source in DEMO_MODE and as fallback when NOAA API fails.
"""
from backend.seed import BASELINE_CLIMATE


def get_mock_climate(region_id: str) -> dict | None:
    """Return mock climate data for a region, or None if region unknown.

    Returns dict with keys: temperature_anomaly, drought_index,
    rainfall_anomaly, ndvi_score, soil_moisture.
    """
    data = BASELINE_CLIMATE.get(region_id)
    if data is None:
        return None
    # Return a copy so callers can't mutate the source
    return dict(data)
