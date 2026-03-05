"""
Climate Ingestion Service
─────────────────────────
Tries real sources first, silently falls back to mock if anything fails.
PRD requirement: demo must never crash due to external API failure.

Live data sources:
  1. NOAA CDO  → temperature_anomaly_c, rainfall_anomaly_pct  (needs NOAA_TOKEN)
  2. Open-Meteo → soil_moisture (free, no key)
  3. Open-Meteo → NDVI proxy via ET₀ / reference evapotranspiration (free, no key)
  4. US Drought Monitor → drought_index (free, no key)
"""

from __future__ import annotations

import logging
import math
import os
import time
from typing import Any, Dict, Optional

import httpx

from .mock_data import get_mock_climate

logger = logging.getLogger(__name__)

# ── In-memory cache: region_id → (timestamp, snapshot_dict) ─────────────
_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_get(region_id: str) -> Optional[Dict[str, Any]]:
    entry = _cache.get(region_id)
    if entry and (time.time() - entry[0]) < CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(region_id: str, snapshot: Dict[str, Any]) -> None:
    _cache[region_id] = (time.time(), snapshot)


def clear_ingestion_cache() -> None:
    """Clear the in-memory climate ingestion cache so next requests pull fresh live data."""
    _cache.clear()


# ── NOAA fetch (optional — enriches temp + rainfall if token exists) ────
NOAA_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2"


def _get_noaa_token() -> str:
    """Read token at call time so load_dotenv() has run first."""
    return os.getenv("NOAA_TOKEN", "")


def _try_noaa(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """
    Attempt to pull recent temperature + precipitation normals from NOAA CDO.
    Returns a partial dict with temperature_anomaly_c and rainfall_anomaly_pct,
    or None if anything fails.
    """
    noaa_token = _get_noaa_token()
    if not noaa_token:
        logger.info("NOAA_TOKEN not set — skipping real fetch")
        return None

    try:
        # Find nearest station WITH recent data
        headers = {"token": noaa_token}
        extent = f"{lat - 0.5},{lng - 0.5},{lat + 0.5},{lng + 0.5}"
        end_date = time.strftime("%Y-%m-%d")
        start_date = time.strftime(
            "%Y-%m-%d", time.gmtime(time.time() - 30 * 86400)
        )
        station_resp = httpx.get(
            f"{NOAA_BASE}/stations",
            headers=headers,
            params={
                "extent": extent,
                "datasetid": "GHCND",
                "startdate": start_date,
                "enddate": end_date,
                "limit": 5,
            },
            timeout=5.0,
        )
        station_resp.raise_for_status()
        stations = station_resp.json().get("results", [])
        if not stations:
            logger.warning("NOAA: no active station near %.2f, %.2f", lat, lng)
            return None

        station_id = stations[0]["id"]
        logger.info("NOAA: using station %s", station_id)

        # Pull recent daily data (last 30 days)
        data_resp = httpx.get(
            f"{NOAA_BASE}/data",
            headers=headers,
            params={
                "datasetid": "GHCND",
                "stationid": station_id,
                "startdate": start_date,
                "enddate": end_date,
                "datatypeid": "TAVG,TMAX,TMIN,PRCP",
                "units": "metric",
                "limit": 200,
            },
            timeout=8.0,
        )
        data_resp.raise_for_status()
        results = data_resp.json().get("results", [])

        tavg_vals = [r["value"] for r in results if r["datatype"] == "TAVG"]
        tmax_vals = [r["value"] for r in results if r["datatype"] == "TMAX"]
        tmin_vals = [r["value"] for r in results if r["datatype"] == "TMIN"]
        prcp_vals = [r["value"] for r in results if r["datatype"] == "PRCP"]

        out: Dict[str, Any] = {}

        # Temperature: prefer TAVG, fall back to (TMAX+TMIN)/2
        if tavg_vals:
            mean_temp = sum(tavg_vals) / len(tavg_vals) / 10  # tenths °C → °C
            out["temperature_anomaly_c"] = round(mean_temp - 15.0, 2)
        elif tmax_vals and tmin_vals:
            avg_max = sum(tmax_vals) / len(tmax_vals) / 10
            avg_min = sum(tmin_vals) / len(tmin_vals) / 10
            mean_temp = (avg_max + avg_min) / 2
            out["temperature_anomaly_c"] = round(mean_temp - 15.0, 2)

        if prcp_vals:
            # PRCP is already in mm (metric units), not tenths
            mean_prcp = sum(prcp_vals) / len(prcp_vals)
            # Rough anomaly vs 2.5mm/day "normal"
            out["rainfall_anomaly_pct"] = round(
                ((mean_prcp - 2.5) / 2.5) * 100, 1
            )

        if out:
            logger.info("NOAA returned %d fields for station %s", len(out), station_id)
            return out

        return None

    except Exception as exc:
        logger.warning("NOAA fetch failed (silent fallback): %s", exc)
        return None


# ── Open-Meteo: soil moisture + NDVI proxy + drought proxy (free, no key) ─

def _try_open_meteo(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """
    Fetch real soil moisture and reference evapotranspiration from
    Open-Meteo's historical archive API (has actual measured soil moisture).
    Also derives a drought proxy from precipitation deficit.
    """
    try:
        end_date = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 2 * 86400))
        start_date = time.strftime(
            "%Y-%m-%d", time.gmtime(time.time() - 10 * 86400)
        )
        resp = httpx.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lng,
                "daily": "soil_moisture_0_to_7cm_mean,et0_fao_evapotranspiration,precipitation_sum",
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "auto",
            },
            timeout=8.0,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})

        out: Dict[str, Any] = {}

        # Soil moisture: Open-Meteo gives m³/m³ (0.0–0.6 typical)
        # Convert to 0–100 scale: divide by 0.45 (field capacity) and ×100
        sm_vals = [v for v in (daily.get("soil_moisture_0_to_7cm_mean") or []) if v is not None]
        if sm_vals:
            avg_sm = sum(sm_vals) / len(sm_vals)
            soil_pct = min(100.0, max(0.0, (avg_sm / 0.45) * 100))
            out["soil_moisture"] = round(soil_pct, 1)
            logger.info("Open-Meteo soil moisture: %.3f m³/m³ → %.1f%%", avg_sm, soil_pct)

        # NDVI proxy from ET₀: reference evapotranspiration (mm/day)
        et_vals = [v for v in (daily.get("et0_fao_evapotranspiration") or []) if v is not None]
        if et_vals:
            avg_et = sum(et_vals) / len(et_vals)
            ndvi_proxy = 10 + 80 * (1 / (1 + math.exp(-1.2 * (avg_et - 3.5))))
            out["ndvi_score"] = round(min(95, max(5, ndvi_proxy)), 1)
            logger.info("Open-Meteo ET₀: %.2f mm/day → NDVI proxy: %.1f", avg_et, out["ndvi_score"])

        # Drought proxy from precipitation deficit
        # Compare recent precip to a "normal" baseline of ~2.5mm/day
        prcp_vals = [v for v in (daily.get("precipitation_sum") or []) if v is not None]
        if prcp_vals:
            avg_prcp = sum(prcp_vals) / len(prcp_vals)
            normal_prcp = 2.5  # approximate global daily average mm
            # Drought index: 0 = no drought (plenty of rain), 100 = extreme drought
            if avg_prcp >= normal_prcp:
                drought_idx = max(0, 15 - (avg_prcp - normal_prcp) * 3)
            else:
                deficit_ratio = (normal_prcp - avg_prcp) / normal_prcp
                drought_idx = 15 + deficit_ratio * 85
            out["drought_index"] = round(min(100.0, max(0.0, drought_idx)), 1)
            logger.info(
                "Open-Meteo precip: %.2f mm/day → drought index: %.1f",
                avg_prcp, out["drought_index"],
            )

        return out if out else None

    except Exception as exc:
        logger.warning("Open-Meteo fetch failed (silent fallback): %s", exc)
        return None


# ── Public API ──────────────────────────────────────────────────────────
def get_climate_snapshot(
    region_id: str,
    lat: float = 0.0,
    lng: float = 0.0,
) -> Dict[str, Any]:
    """
    Returns a full climate snapshot for a region.
    Always succeeds — uses mock fallback if real APIs fail.

    Data sources (tried in order, each independent):
      1. NOAA CDO       → temperature_anomaly_c, rainfall_anomaly_pct
      2. Open-Meteo     → soil_moisture, ndvi_score (ET₀ proxy), drought_index
      4. Mock fallback  → any field not filled by real APIs
    """
    # 1. Check cache first
    cached = _cache_get(region_id)
    if cached:
        return cached

    # 2. Start with mock baseline (guaranteed values for all fields)
    snapshot = get_mock_climate(region_id)
    live_sources: list[str] = []

    # 3. Try to enrich with real NOAA data (temp + rainfall)
    noaa_data = _try_noaa(lat, lng)
    if noaa_data:
        snapshot.update(noaa_data)
        live_sources.append("noaa")

    # 4. Try Open-Meteo for soil moisture + NDVI proxy + drought index
    meteo_data = _try_open_meteo(lat, lng)
    if meteo_data:
        snapshot.update(meteo_data)
        live_sources.append("open-meteo")

    # 5. Set source label
    if live_sources:
        snapshot["source"] = "+".join(live_sources)
    else:
        snapshot["source"] = "mock"

    logger.info(
        "Climate snapshot for %s: sources=[%s], temp=%.2f, drought=%.1f, rain=%.1f, ndvi=%.1f, soil=%.1f",
        region_id,
        snapshot["source"],
        snapshot.get("temperature_anomaly_c", 0),
        snapshot.get("drought_index", 0),
        snapshot.get("rainfall_anomaly_pct", 0),
        snapshot.get("ndvi_score", 0),
        snapshot.get("soil_moisture", 0),
    )

    # 6. Cache and return
    _cache_set(region_id, snapshot)
    return snapshot

