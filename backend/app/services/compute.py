"""
Orchestrator — compute_all()
─────────────────────────────
Single function that runs the full TerraLend pipeline for a region:
  ingestion → (apply overrides) → normalize → stress → finance

Every endpoint calls this so numbers are always consistent.

Step 12 additions:
  - TTL cache for slider responsiveness (12A)
  - Nearest-region fallback when climate data missing (12B)
  - model_version tag for explainability (12F)
  - Performance timing (12G)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.db import get_conn
from app.services.cache import compute_cache
from app.services.ingestion import get_climate_snapshot
from app.services.normalize import normalize_all
from app.services.stress import compute_yield_stress
from app.services.finance import compute_financial, RegionBase

logger = logging.getLogger(__name__)

MODEL_VERSION = "terralend_stress_v1.0"


# ── Override clamping ranges ────────────────────────────────────────────
_OVERRIDE_RANGES: Dict[str, tuple[float, float]] = {
    "temperature_anomaly_c": (-5.0, 8.0),
    "drought_index":         (0.0, 100.0),
    "rainfall_anomaly_pct":  (-100.0, 100.0),
    "ndvi_score":            (0.0, 100.0),
    "soil_moisture":         (0.0, 100.0),
}


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _apply_overrides(
    snapshot: Dict[str, Any],
    overrides: Dict[str, float],
) -> Dict[str, Any]:
    """
    Apply simulation slider overrides to a climate snapshot.
    Only known keys are applied; values are clamped to safe ranges.
    """
    result = dict(snapshot)  # shallow copy
    for key, value in overrides.items():
        if key in _OVERRIDE_RANGES:
            lo, hi = _OVERRIDE_RANGES[key]
            result[key] = round(_clamp(float(value), lo, hi), 2)
    return result


# ── Static "old system" baseline (never changes) ───────────────────────
_OLD_SYSTEM_BASELINE = {
    "label": "Traditional Annual Review",
    "description": "Static risk assessment updated once per year, no climate inputs.",
    "pd_markup": 0.0,          # no climate adjustment
    "rate_markup": 0.0,
    "premium_markup": 0.0,
    "update_frequency": "annual",
}


def get_region(region_id: str) -> Optional[dict]:
    """Fetch a region row from SQLite. Returns None if not found."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM regions WHERE region_id = ?", (region_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _get_all_regions() -> List[dict]:
    """Fetch all region rows (for nearest-region lookup)."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM regions").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _find_nearest_region(
    target_lat: float,
    target_lng: float,
    exclude_id: str,
) -> Optional[dict]:
    """
    Find the nearest region by squared Euclidean distance (Step 12B).
    Good enough for demo — no Haversine needed.
    """
    regions = _get_all_regions()
    best, best_dist = None, float("inf")
    for r in regions:
        if r["region_id"] == exclude_id:
            continue
        dist = (r["lat"] - target_lat) ** 2 + (r["lng"] - target_lng) ** 2
        if dist < best_dist:
            best, best_dist = r, dist
    return best


def _snapshot_with_nearest_fallback(
    region: dict,
) -> Dict[str, Any]:
    """
    Get climate snapshot. If the snapshot is missing critical data,
    try the nearest region and annotate the response (Step 12B).
    """
    region_id = region["region_id"]
    snapshot = get_climate_snapshot(region_id, region["lat"], region["lng"])

    # Check for missing critical fields (all should exist from mock, but
    # this handles future cases where a data source returns partial data)
    critical_fields = ["temperature_anomaly_c", "drought_index", "ndvi_score"]
    missing = [f for f in critical_fields if snapshot.get(f) is None]

    if missing:
        nearest = _find_nearest_region(region["lat"], region["lng"], region_id)
        if nearest:
            logger.info(
                "Region %s missing %s — falling back to nearest %s",
                region_id, missing, nearest["region_id"],
            )
            snapshot = get_climate_snapshot(
                nearest["region_id"], nearest["lat"], nearest["lng"]
            )
            snapshot["data_source"] = "nearest_region"
            snapshot["nearest_region_id"] = nearest["region_id"]
            snapshot["nearest_region_name"] = nearest["name"]
            snapshot["note"] = (
                "Climate data unavailable for this region, "
                f"using nearest region ({nearest['name']})"
            )

    return snapshot


def compute_all(
    region_id: str,
    overrides: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Run the full TerraLend pipeline for a region.

    Parameters
    ----------
    region_id : str
        Region to compute for.
    overrides : dict, optional
        Slider values from /simulate that override climate snapshot fields.

    Returns
    -------
    dict with keys:
        region, climate, normalized_indices, stress, financial, comparison,
        meta (model_version, compute_ms)
    """
    # ── 12A: check cache first ──────────────────────────────────────────
    cache_key = compute_cache.make_key(region_id, overrides)
    cached = compute_cache.get(cache_key)
    if cached is not None:
        logger.debug("cache HIT for %s", cache_key)
        return cached

    # ── 12G: start timer ────────────────────────────────────────────────
    t0 = time.perf_counter()

    region = get_region(region_id)
    if region is None:
        return None

    # 1) Fetch climate — with nearest-region fallback (12B)
    snapshot = _snapshot_with_nearest_fallback(region)

    # 2) Apply simulation overrides (if any)
    if overrides:
        snapshot = _apply_overrides(snapshot, overrides)

    # 3) Normalize raw values → 0–100 stress indices
    indices = normalize_all(snapshot)

    # 4) Compute yield stress score + contributions
    stress = compute_yield_stress(indices)

    # 5) Compute financial outputs
    region_base = RegionBase(
        base_loan_rate=region["base_loan_rate"],
        base_pd=region["base_pd"],
        base_premium=region["base_premium"],
    )
    financial = compute_financial(region_base, stress["yield_stress_score"])

    # 6) Build "old system" comparison (static baseline)
    comparison = {
        "old_system": {
            **_OLD_SYSTEM_BASELINE,
            "pd": region["base_pd"],
            "interest_rate": region["base_loan_rate"],
            "insurance_premium": region["base_premium"],
        },
        "terralend": {
            "pd": financial["pd"],
            "interest_rate": financial["interest_rate"],
            "insurance_premium": financial["insurance_premium"],
            "repayment_flexibility_score": financial["repayment_flexibility_score"],
            "yield_stress_score": stress["yield_stress_score"],
            "dominant_factor": stress["dominant_factor"],
            "update_frequency": "real-time",
        },
    }

    # ── 12G: end timer ──────────────────────────────────────────────────
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    logger.info("compute_all(%s) took %.1fms", region_id, elapsed_ms)

    result = {
        "region": region,
        "climate": snapshot,
        "normalized_indices": indices,
        "stress": stress,
        "financial": financial,
        "comparison": comparison,
        # 12F: model version + timing for explainability
        "meta": {
            "model_version": MODEL_VERSION,
            "compute_ms": elapsed_ms,
        },
    }

    # ── 12A: store in cache ─────────────────────────────────────────────
    compute_cache.set(cache_key, result)

    return result
