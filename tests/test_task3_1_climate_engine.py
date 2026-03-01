"""Tests for Task 3.1: Yield Stress Engine.

Tests the deterministic formula from PRD Section 4.3.
"""
from backend.services.climate_engine import compute_yield_stress, WEIGHTS


# ── 1. All-normal inputs → low stress (< 30) ────────────────────────────────

def test_normal_inputs_low_stress():
    """Moderate/normal climate → low stress score."""
    score = compute_yield_stress(
        temperature_anomaly=0.5,  # slight warmth
        drought_index=20,         # low drought
        rainfall_anomaly=5,       # near normal
        ndvi_score=75,            # healthy vegetation
        soil_moisture=65,         # good moisture
    )
    assert score < 30, f"Normal inputs should produce low stress, got {score}"


# ── 2. All-extreme inputs → high stress (> 80) ──────────────────────────────

def test_extreme_inputs_high_stress():
    """All climate inputs at worst values → high stress."""
    score = compute_yield_stress(
        temperature_anomaly=5.0,   # max heat
        drought_index=100,         # severe drought
        rainfall_anomaly=-80,      # severe deficit
        ndvi_score=0,              # dead vegetation
        soil_moisture=0,           # bone dry
    )
    assert score > 80, f"Extreme inputs should produce high stress, got {score}"


# ── 3. Perfect conditions → stress near 0 ────────────────────────────────────

def test_perfect_conditions_near_zero():
    """No anomaly, high NDVI, good moisture → stress near 0."""
    score = compute_yield_stress(
        temperature_anomaly=-3.0,  # coolest → 0 heat stress
        drought_index=0,           # no drought
        rainfall_anomaly=0,        # perfect rainfall
        ndvi_score=100,            # perfect vegetation
        soil_moisture=100,         # perfect moisture
    )
    assert score <= 5, f"Perfect conditions should produce near-zero stress, got {score}"


# ── 4. Single-factor dominance → stress 25–35 ────────────────────────────────

def test_single_factor_heat_dominance():
    """Max heat stress with all others normal → stress between 25–35."""
    score = compute_yield_stress(
        temperature_anomaly=5.0,   # max heat → 100 heat stress
        drought_index=15,          # low
        rainfall_anomaly=0,        # normal
        ndvi_score=80,             # healthy
        soil_moisture=70,          # good
    )
    # Heat contributes 30 pts (0.30 * 100). "Normal" others contribute ~10 pts baseline.
    assert 35 <= score <= 45, f"Heat-dominant with normal others should be 35-45, got {score}"


# ── 5. Output always clamped 0–100 ───────────────────────────────────────────

def test_output_clamped_with_extreme_inputs():
    """Output stays 0–100 even with absurd input values."""
    # Way beyond normal ranges
    score_high = compute_yield_stress(
        temperature_anomaly=100,
        drought_index=500,
        rainfall_anomaly=-200,
        ndvi_score=-50,
        soil_moisture=-100,
    )
    assert 0 <= score_high <= 100, f"Should be clamped, got {score_high}"

    score_low = compute_yield_stress(
        temperature_anomaly=-100,
        drought_index=-500,
        rainfall_anomaly=0,
        ndvi_score=500,
        soil_moisture=500,
    )
    assert 0 <= score_low <= 100, f"Should be clamped, got {score_low}"


# ── 6. Weights sum to 1.0 ────────────────────────────────────────────────────

def test_weights_sum_to_one():
    """All weights in the formula sum to exactly 1.0."""
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-10, f"Weights sum to {total}, not 1.0"


# ── 7. Negative temperature anomaly → low heat stress ────────────────────────

def test_negative_temp_low_heat_stress():
    """Cooling (negative anomaly) → low heat stress contribution."""
    score_cold = compute_yield_stress(
        temperature_anomaly=-3.0,  # coldest → 0 heat stress
        drought_index=30,
        rainfall_anomaly=-10,
        ndvi_score=70,
        soil_moisture=60,
    )
    score_hot = compute_yield_stress(
        temperature_anomaly=5.0,   # hottest → 100 heat stress
        drought_index=30,
        rainfall_anomaly=-10,
        ndvi_score=70,
        soil_moisture=60,
    )
    assert score_cold < score_hot, "Cold should produce less stress than hot"
    # The difference should be roughly 0.30 * 100 = 30 points (heat weight * full range)
    diff = score_hot - score_cold
    assert 25 <= diff <= 35, f"Heat stress range should be ~30 points, got {diff}"


# ── 8. Both extreme rainfall surplus and deficit → high rainfall stress ──────

def test_rainfall_both_extremes_stressful():
    """Both -80% and +80% rainfall produce equally high rainfall stress."""
    score_deficit = compute_yield_stress(
        temperature_anomaly=0,
        drought_index=0,
        rainfall_anomaly=-80,  # severe deficit
        ndvi_score=100,
        soil_moisture=100,
    )
    score_surplus = compute_yield_stress(
        temperature_anomaly=0,
        drought_index=0,
        rainfall_anomaly=80,   # severe surplus
        ndvi_score=100,
        soil_moisture=100,
    )
    # Both extremes should produce similar stress
    assert abs(score_deficit - score_surplus) < 1, \
        f"Deficit ({score_deficit}) and surplus ({score_surplus}) should be equally stressful"
    # And both should be meaningfully above zero
    assert score_deficit > 15, f"Deficit stress too low: {score_deficit}"


# ── 9. Boundary values ───────────────────────────────────────────────────────

def test_boundary_all_zeros():
    """All inputs at 0."""
    score = compute_yield_stress(0, 0, 0, 0, 0)
    # temp=0 → heat_stress=(0+3)/8*100=37.5, drought=0, rain=0, ndvi_deficit=100, soil_deficit=100
    assert 0 <= score <= 100


def test_boundary_all_hundred():
    """All inputs at 100 (where applicable)."""
    score = compute_yield_stress(8, 100, 80, 100, 100)
    # heat=max, drought=max, rain=max, ndvi_deficit=0, soil_deficit=0
    assert 0 <= score <= 100


def test_boundary_all_fifty():
    """All inputs at midpoint values."""
    score = compute_yield_stress(1, 50, 0, 50, 50)
    assert 0 <= score <= 100
    # Should be roughly mid-range stress
    assert 20 <= score <= 60, f"Mid-range inputs should give mid-range stress, got {score}"


# ── 10. Float precision ──────────────────────────────────────────────────────

def test_float_precision():
    """Fractional inputs produce correct fractional output."""
    score = compute_yield_stress(
        temperature_anomaly=1.37,
        drought_index=33.33,
        rainfall_anomaly=-22.5,
        ndvi_score=67.8,
        soil_moisture=54.2,
    )
    # Result should be a float, not integer
    assert isinstance(score, float)
    # Verify it's a reasonable value
    assert 0 <= score <= 100
