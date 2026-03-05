"""
Yield Stress Engine
───────────────────
Computes a single 0–100 Yield Stress Score from normalized climate indices
using the PRD-defined weighted formula.

Weights (from PRD):
  Heat stress:          0.30
  Drought:              0.25
  Rainfall anomaly:     0.20
  Vegetation (NDVI):    0.15
  Soil moisture deficit: 0.10
"""

from __future__ import annotations

from typing import Dict, Optional


DEFAULT_WEIGHTS: Dict[str, float] = {
    "heat":     0.30,
    "drought":  0.25,
    "rainfall": 0.20,
    "ndvi":     0.15,
    "soil":     0.10,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def compute_yield_stress(
    indices: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """
    Compute yield stress score (0–100) from normalized climate stress indices.

    Expected keys in `indices` (all 0–100, higher = MORE stress):
        heat_index          – from normalize.heat_stress_index()
        drought_index       – from normalize.drought_index_to_stress()
        rainfall_index      – from normalize.rainfall_stress_index()
        ndvi_stress         – from normalize.ndvi_health_to_stress()  (already inverted)
        soil_moisture_stress – from normalize.soil_moisture_to_stress() (already inverted)

    Returns dict with:
        yield_stress_score  – 0–100
        dominant_factor     – name of the biggest contributor
        contributions       – per-factor weighted contribution
        inputs_used         – the clamped indices that went into the calc
        weights_used        – the weights applied
    """
    w = weights or DEFAULT_WEIGHTS

    # Pull values (all are already "stress" indices from normalize.py)
    heat     = _clamp(float(indices.get("heat_index", 0.0)))
    drought  = _clamp(float(indices.get("drought_index", 0.0)))
    rainfall = _clamp(float(indices.get("rainfall_index", 0.0)))
    ndvi     = _clamp(float(indices.get("ndvi_stress", 0.0)))
    soil     = _clamp(float(indices.get("soil_moisture_stress", 0.0)))

    # Per-factor weighted contributions
    contributions = {
        "heat":     round(w["heat"]     * heat,     2),
        "drought":  round(w["drought"]  * drought,  2),
        "rainfall": round(w["rainfall"] * rainfall, 2),
        "ndvi":     round(w["ndvi"]     * ndvi,     2),
        "soil":     round(w["soil"]     * soil,     2),
    }

    # Weighted sum → final score
    score = _clamp(sum(contributions.values()))

    # Which factor is driving the most stress?
    dominant_factor = max(contributions, key=lambda k: contributions[k])

    return {
        "yield_stress_score": round(score, 2),
        "dominant_factor": dominant_factor,
        "contributions": contributions,
        "inputs_used": {
            "heat_index":           round(heat, 2),
            "drought_index":        round(drought, 2),
            "rainfall_index":       round(rainfall, 2),
            "ndvi_stress":          round(ndvi, 2),
            "soil_moisture_stress": round(soil, 2),
        },
        "weights_used": w,
    }
