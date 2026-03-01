"""NOAA Climate Data Online (CDO) API client.

Fetches recent temperature and precipitation data, normalizes to our index scales.
Returns None on any failure — the orchestrator falls back to mock data.

Uses a two-step approach:
  1. Find nearby GHCND stations via /stations?extent=...  (cached indefinitely)
  2. Fetch data for those stations via /data?stationid=... (cached 5 minutes)
"""
import logging
import time as _time
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

NOAA_BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2"
TIMEOUT_SECONDS = 15.0

# Seasonal baseline assumptions for normalization
SEASONAL_TEMP_BASELINE_C = 20.0  # approximate summer norm in °C
SEASONAL_PRECIP_BASELINE_MM = 80.0  # approximate monthly norm in mm

# Caches
_station_cache: dict[tuple[float, float], list[str]] = {}  # (lat,lng) -> [stationId, ...]
_data_cache: dict[str, tuple[float, dict]] = {}  # cache_key -> (timestamp, normalized_data)
DATA_CACHE_TTL = 300  # 5 minutes


async def _find_nearby_stations(
    lat: float, lng: float, api_key: str
) -> list[str]:
    """Find GHCND stations near a lat/lng using the stations endpoint.

    Returns a list of station IDs, or empty list on failure.
    Results are cached indefinitely (stations don't move).
    """
    cache_key = (round(lat, 2), round(lng, 2))
    if cache_key in _station_cache:
        return _station_cache[cache_key]

    params = {
        "datasetid": "GHCND",
        "extent": f"{lat - 1.0},{lng - 1.0},{lat + 1.0},{lng + 1.0}",
        "limit": 25,
        "sortfield": "datacoverage",
        "sortorder": "desc",
    }
    headers = {"token": api_key}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(
                f"{NOAA_BASE_URL}/stations", params=params, headers=headers
            )
            if resp.status_code != 200:
                logger.warning(f"NOAA stations API returned {resp.status_code}")
                return []

            data = resp.json()
            results = data.get("results", [])
            # Filter to stations with recent data and decent coverage
            station_ids = [
                r["id"]
                for r in results
                if r.get("datacoverage", 0) > 0.3
                and r.get("maxdate", "") >= "2024-01-01"
            ]
            if not station_ids:
                # Fallback: use any station returned
                station_ids = [r["id"] for r in results[:5]]

            _station_cache[cache_key] = station_ids
            logger.info(
                f"Found {len(station_ids)} NOAA stations near ({lat}, {lng})"
            )
            return station_ids

    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"NOAA stations lookup failed: {e}")
        return []


async def fetch_noaa_data(lat: float, lng: float, api_key: str) -> dict | None:
    """Fetch recent climate data from NOAA CDO API.

    Returns a dict with available climate fields normalized to our scales,
    or None if the request fails for any reason.

    Available fields from NOAA: temperature_anomaly, drought_index, rainfall_anomaly.
    Fields NOT available from NOAA (returned as None): ndvi_score, soil_moisture.
    """
    if not api_key:
        logger.warning("No NOAA API key provided, skipping NOAA fetch")
        return None

    # Check data cache first
    cache_key = f"{round(lat, 2)},{round(lng, 2)}"
    if cache_key in _data_cache:
        ts, cached_data = _data_cache[cache_key]
        if _time.time() - ts < DATA_CACHE_TTL:
            logger.info(f"Using cached NOAA data for ({lat}, {lng})")
            return cached_data

    # Step 1: Find nearby stations
    station_ids = await _find_nearby_stations(lat, lng, api_key)
    if not station_ids:
        logger.warning(f"No NOAA stations found near ({lat}, {lng})")
        return None

    # Step 2: Fetch data for those stations
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Use up to 5 stations to get a good sample of all data types
    station_filter = "&".join(
        f"stationid={sid}" for sid in station_ids[:5]
    )

    params = {
        "datasetid": "GHCND",
        "datatypeid": "TMAX,TMIN,PRCP",
        "startdate": start_date.strftime("%Y-%m-%d"),
        "enddate": end_date.strftime("%Y-%m-%d"),
        "units": "metric",
        "limit": 200,
        "sortfield": "date",
        "sortorder": "desc",
    }
    # Add station IDs individually (httpx handles repeated keys)
    for sid in station_ids[:3]:
        # httpx doesn't support repeated query keys via dict,
        # so we'll build the URL manually
        pass

    headers = {"token": api_key}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            # Build URL with repeated stationid params
            base_url = f"{NOAA_BASE_URL}/data"
            query_parts = [f"{k}={v}" for k, v in params.items()]
            for sid in station_ids[:5]:
                query_parts.append(f"stationid={sid}")
            full_url = f"{base_url}?{'&'.join(query_parts)}"

            resp = await client.get(full_url, headers=headers)

            if resp.status_code == 429:
                logger.warning("NOAA API rate limited (429)")
                return None

            if resp.status_code != 200:
                logger.warning(f"NOAA API returned status {resp.status_code}")
                return None

            data = resp.json()
            result = _normalize_noaa_response(data)

            # Cache successful results
            if result:
                _data_cache[cache_key] = (_time.time(), result)

            return result

    except httpx.TimeoutException:
        logger.warning("NOAA API request timed out")
        return None
    except httpx.RequestError as e:
        logger.warning(f"NOAA API network error: {e}")
        return None
    except Exception as e:
        logger.warning(f"NOAA API unexpected error: {e}")
        return None


def _normalize_noaa_response(data: dict) -> dict | None:
    """Normalize raw NOAA response into our climate index scales.

    Returns None if response is malformed or missing required data.
    """
    results = data.get("results")
    if not results:
        logger.warning("NOAA response missing 'results' field")
        return None

    # Aggregate raw values
    temps = []
    precip_values = []

    for record in results:
        datatype = record.get("datatype")
        value = record.get("value")
        if value is None:
            continue
        if datatype in ("TMAX", "TMIN"):
            temps.append(value)
        elif datatype == "PRCP":
            precip_values.append(value)

    if not temps:
        logger.warning("NOAA response has no temperature data")
        return None

    # Compute temperature anomaly (°C deviation from seasonal baseline)
    avg_temp = sum(temps) / len(temps)
    temperature_anomaly = avg_temp - SEASONAL_TEMP_BASELINE_C
    # Clamp to our range: -5 to +8
    temperature_anomaly = max(-5.0, min(8.0, temperature_anomaly))

    # Compute rainfall anomaly and drought index from precipitation
    if precip_values:
        total_precip = sum(precip_values)
        # rainfall_anomaly: % deviation from baseline (-80 to +80)
        if SEASONAL_PRECIP_BASELINE_MM > 0:
            rain_pct = ((total_precip - SEASONAL_PRECIP_BASELINE_MM) / SEASONAL_PRECIP_BASELINE_MM) * 100
        else:
            rain_pct = 0.0
        rainfall_anomaly = max(-80.0, min(80.0, rain_pct))

        # drought_index: low precipitation → high drought (0–100)
        # 0mm → 100 drought, baseline mm → ~20 drought, 2x baseline → 0 drought
        precip_ratio = total_precip / SEASONAL_PRECIP_BASELINE_MM if SEASONAL_PRECIP_BASELINE_MM > 0 else 0
        drought_index = max(0.0, min(100.0, (1.0 - precip_ratio) * 100))
    else:
        rainfall_anomaly = 0.0
        drought_index = 50.0  # unknown → assume moderate

    return {
        "temperature_anomaly": round(temperature_anomaly, 2),
        "drought_index": round(drought_index, 2),
        "rainfall_anomaly": round(rainfall_anomaly, 2),
        "ndvi_score": None,       # Not available from NOAA
        "soil_moisture": None,    # Not available from NOAA
    }
