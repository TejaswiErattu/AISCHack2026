"""Yield Stress Engine.

Deterministic formula that converts 5 climate inputs into a single
yield_stress_score (0–100, higher = more stressed). No AI/ML — pure math.

Formula from PRD Section 4.3.
"""

# Weights for the composite stress score (must sum to 1.0)
WEIGHTS = {
    "heat_stress": 0.30,
    "drought": 0.25,
    "rainfall": 0.20,
    "ndvi_deficit": 0.15,
    "soil_deficit": 0.10,
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_yield_stress(
    temperature_anomaly: float,
    drought_index: float,
    rainfall_anomaly: float,
    ndvi_score: float,
    soil_moisture: float,
) -> float:
    """Compute yield stress score from 5 climate inputs.

    Args:
        temperature_anomaly: °C above/below seasonal norm (-5 to +8 typical)
        drought_index: 0–100 (higher = more drought)
        rainfall_anomaly: % deviation from seasonal avg (-80 to +80)
        ndvi_score: 0–100 vegetation health (higher = healthier)
        soil_moisture: 0–100 (higher = wetter)

    Returns:
        yield_stress_score: 0–100 (higher = more stressed)
    """
    # Sub-index 1: Heat stress
    # -3°C → 0, +5°C → 100, linear interpolation
    heat_stress = _clamp((temperature_anomaly + 3) / 8 * 100, 0, 100)

    # Sub-index 2: Drought (already 0–100)
    drought = _clamp(drought_index, 0, 100)

    # Sub-index 3: Rainfall anomaly stress
    # Both extremes are stressful — deviation from 0 = stress
    # abs(-80%) → 100, abs(0%) → 0, abs(+80%) → 100
    rainfall_stress = _clamp(abs(rainfall_anomaly) / 80 * 100, 0, 100)

    # Sub-index 4: NDVI deficit (low vegetation = high stress)
    ndvi_deficit = _clamp(100 - ndvi_score, 0, 100)

    # Sub-index 5: Soil moisture deficit (low moisture = high stress)
    soil_deficit = _clamp(100 - soil_moisture, 0, 100)

    # Weighted composite
    stress = (
        WEIGHTS["heat_stress"] * heat_stress
        + WEIGHTS["drought"] * drought
        + WEIGHTS["rainfall"] * rainfall_stress
        + WEIGHTS["ndvi_deficit"] * ndvi_deficit
        + WEIGHTS["soil_deficit"] * soil_deficit
    )

    return round(_clamp(stress, 0, 100), 2)


def compute_stress_breakdown(
    temperature_anomaly: float,
    drought_index: float,
    rainfall_anomaly: float,
    ndvi_score: float,
    soil_moisture: float,
) -> dict:
    """Return the breakdown of each factor's weighted contribution.

    Useful for the stress endpoint to show which factors contribute most.
    """
    heat_stress = _clamp((temperature_anomaly + 3) / 8 * 100, 0, 100)
    drought = _clamp(drought_index, 0, 100)
    rainfall_stress = _clamp(abs(rainfall_anomaly) / 80 * 100, 0, 100)
    ndvi_deficit = _clamp(100 - ndvi_score, 0, 100)
    soil_deficit = _clamp(100 - soil_moisture, 0, 100)

    return {
        "heat_stress": round(WEIGHTS["heat_stress"] * heat_stress, 2),
        "drought": round(WEIGHTS["drought"] * drought, 2),
        "rainfall_anomaly": round(WEIGHTS["rainfall"] * rainfall_stress, 2),
        "ndvi_deficit": round(WEIGHTS["ndvi_deficit"] * ndvi_deficit, 2),
        "soil_moisture_deficit": round(WEIGHTS["soil_deficit"] * soil_deficit, 2),
    }
