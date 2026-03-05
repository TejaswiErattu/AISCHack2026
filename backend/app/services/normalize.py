"""
Normalization pipeline
─────────────────────
Converts raw climate values (mixed units) into 0–100 stress indices
so the Yield Stress Engine can combine them consistently.

Convention: 0 = no stress, 100 = maximum stress.
"""

from __future__ import annotations


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def linear_map(
    x: float,
    in_min: float,
    in_max: float,
    out_min: float = 0.0,
    out_max: float = 100.0,
) -> float:
    """
    Maps x from [in_min, in_max] into [out_min, out_max] linearly.
    Clamps x to input range first.
    """
    if in_max == in_min:
        return out_min
    if x < in_min:
        x = in_min
    if x > in_max:
        x = in_max
    ratio = (x - in_min) / (in_max - in_min)
    return out_min + ratio * (out_max - out_min)


# ── Individual stress index functions ───────────────────────────────────

def heat_stress_index(temp_anomaly_c: float) -> float:
    """
    Higher temp anomaly => higher stress.
    -2°C anomaly => 0 stress, +5°C anomaly => 100 stress.
    """
    return round(clamp(linear_map(temp_anomaly_c, in_min=-2.0, in_max=5.0)), 1)


def rainfall_stress_index(rainfall_anomaly_pct: float) -> float:
    """
    Rainfall anomaly: negative means drier than normal.
    For MVP: only penalize dryness strongly.
    -80% => 100 stress, 0% => 0 stress, positive => 0 stress.
    """
    if rainfall_anomaly_pct >= 0:
        return 0.0
    return round(
        clamp(
            linear_map(
                rainfall_anomaly_pct,
                in_min=-80.0,
                in_max=0.0,
                out_min=100.0,
                out_max=0.0,
            )
        ),
        1,
    )


def ndvi_health_to_stress(ndvi_score: float) -> float:
    """
    NDVI: higher means healthier vegetation.
    Invert: 100 health => 0 stress, 0 health => 100 stress.
    Handles both 0–1 and 0–100 scales.
    """
    if 0.0 <= ndvi_score <= 1.2:
        ndvi_score = ndvi_score * 100.0
    ndvi_score = clamp(ndvi_score)
    return round(100.0 - ndvi_score, 1)


def soil_moisture_to_stress(soil_moisture: float) -> float:
    """
    Soil moisture: higher is better.
    Invert: 100 moisture => 0 stress, 0 moisture => 100 stress.
    """
    soil_moisture = clamp(soil_moisture)
    return round(100.0 - soil_moisture, 1)


def drought_index_to_stress(drought_index: float) -> float:
    """
    Drought index already 0–100 where higher => worse.
    Pass through with clamp.
    """
    return round(clamp(drought_index), 1)


# ── Master normalizer ──────────────────────────────────────────────────

def normalize_all(raw: dict) -> dict:
    """
    Takes a raw climate snapshot dict (from ingestion) and returns
    a dict of normalized 0–100 stress indices.

    Input keys (from mock_data / ingestion):
        temperature_anomaly_c, rainfall_anomaly_pct,
        drought_index, ndvi_score, soil_moisture

    Output keys:
        heat_index, rainfall_index, drought_index,
        ndvi_stress, soil_moisture_stress
    """
    return {
        "heat_index": heat_stress_index(
            float(raw["temperature_anomaly_c"])
        ),
        "rainfall_index": rainfall_stress_index(
            float(raw["rainfall_anomaly_pct"])
        ),
        "drought_index": drought_index_to_stress(
            float(raw["drought_index"])
        ),
        "ndvi_stress": ndvi_health_to_stress(
            float(raw["ndvi_score"])
        ),
        "soil_moisture_stress": soil_moisture_to_stress(
            float(raw["soil_moisture"])
        ),
    }
