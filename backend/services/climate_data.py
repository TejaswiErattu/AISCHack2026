"""Climate data orchestrator.

Single entry point for getting climate data for any region.
Routes to mock data or NOAA API based on DEMO_MODE config.
Always returns a complete dict with all 5 climate fields.
"""
import logging
import time as _time

from backend.config import settings
from backend.services.mock_data import get_mock_climate
from backend.services.noaa_client import fetch_noaa_data

logger = logging.getLogger(__name__)

# In-memory cache to deduplicate concurrent requests for the same region
_climate_cache: dict[str, tuple[float, dict]] = {}
_CLIMATE_CACHE_TTL = 60  # seconds


async def get_climate_data(region_id: str, lat: float, lng: float) -> dict:
    """Get climate data for a region from the best available source.

    Priority:
      1. DEMO_MODE=true → mock data directly
      2. DEMO_MODE=false → try NOAA, fill gaps from mock, fall back to mock on failure

    Always returns a dict with keys: temperature_anomaly, drought_index,
    rainfall_anomaly, ndvi_score, soil_moisture.
    """
    mock = get_mock_climate(region_id)

    if settings.DEMO_MODE:
        logger.info(f"[{region_id}] Using mock climate data (DEMO_MODE=true)")
        return mock

    # Check orchestrator-level cache (deduplicates concurrent parallel requests)
    if region_id in _climate_cache:
        ts, cached = _climate_cache[region_id]
        if _time.time() - ts < _CLIMATE_CACHE_TTL:
            logger.info(f"[{region_id}] Using cached climate data (orchestrator cache)")
            return cached

    # Try NOAA API
    noaa = await fetch_noaa_data(lat, lng, settings.NOAA_API_KEY)

    if noaa is None:
        logger.info(f"[{region_id}] NOAA failed, falling back to mock data")
        return mock

    # NOAA succeeded — merge with mock for fields NOAA doesn't provide
    result = {
        "temperature_anomaly": noaa["temperature_anomaly"],
        "drought_index": noaa["drought_index"],
        "rainfall_anomaly": noaa["rainfall_anomaly"],
        "ndvi_score": noaa["ndvi_score"] if noaa["ndvi_score"] is not None else mock["ndvi_score"],
        "soil_moisture": noaa["soil_moisture"] if noaa["soil_moisture"] is not None else mock["soil_moisture"],
    }
    _climate_cache[region_id] = (_time.time(), result)
    logger.info(f"[{region_id}] Using NOAA data (mock fill for ndvi/soil_moisture)")
    return result
