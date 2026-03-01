"""Tests for Task 4.1: Financial Risk Translator.

Tests the deterministic formulas from PRD Section 4.4.
"""
from backend.services.financial_translator import translate_financial

# Standard base values (Central Valley CA)
BASE_RATE = 5.5
BASE_PD = 0.05
BASE_PREMIUM = 1200.0

ALL_KEYS = {"interest_rate", "probability_of_default", "insurance_premium", "repayment_flexibility"}


# ── 1. Zero stress → outputs near base values ────────────────────────────────

def test_zero_stress_near_base():
    """Zero stress → outputs near base values."""
    result = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 0.0)
    # PD = 0.05 + 0 = 0.05
    assert result["probability_of_default"] == 0.05
    # interest_rate = 5.5 + (0.05 * 0.08 * 100) = 5.5 + 0.4 = 5.9
    assert result["interest_rate"] == 5.9
    # insurance_premium = 1200 * (1 + 0) = 1200
    assert result["insurance_premium"] == 1200.0
    # repayment_flexibility = 100 - 0 = 100
    assert result["repayment_flexibility"] == 100.0


# ── 2. Max stress (100) → outputs at upper bounds ────────────────────────────

def test_max_stress_upper_bounds():
    """Max stress (100) → outputs approach or hit upper bounds."""
    result = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 100.0)
    # PD = 0.05 + 0.25 = 0.30
    assert result["probability_of_default"] == 0.30
    # interest_rate = 5.5 + (0.30 * 8.0) = 5.5 + 2.4 = 7.9 (under 15% cap)
    assert result["interest_rate"] == 7.9
    # insurance_premium = 1200 * 2.0 = 2400
    assert result["insurance_premium"] == 2400.0
    # repayment_flexibility = 100 - 100 = 0
    assert result["repayment_flexibility"] == 0.0


# ── 3. Mid stress (50) → proportionally between min and max ──────────────────

def test_mid_stress_proportional():
    """Mid stress (50) → outputs proportionally between base and max."""
    result = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 50.0)
    # PD = 0.05 + 0.125 = 0.175
    assert result["probability_of_default"] == 0.175
    # interest_rate = 5.5 + (0.175 * 8.0) = 5.5 + 1.4 = 6.9
    assert result["interest_rate"] == 6.9
    # insurance_premium = 1200 * 1.5 = 1800
    assert result["insurance_premium"] == 1800.0
    # repayment_flexibility = 50
    assert result["repayment_flexibility"] == 50.0


# ── 4. Clamping: artificially high stress doesn't exceed 15% rate ─────────────

def test_clamping_high_stress():
    """Artificially high stress doesn't produce interest_rate > 15%."""
    # Use a high base_rate so the formula would exceed 15% without clamping
    result = translate_financial(12.0, 0.08, 1600.0, 100.0)
    assert result["interest_rate"] <= 15.0
    assert result["probability_of_default"] <= 0.50
    assert result["insurance_premium"] <= 1600.0 * 3.0
    assert result["repayment_flexibility"] >= 0.0


# ── 5. Different base values produce different outputs ────────────────────────

def test_different_base_values():
    """Different base values produce different outputs."""
    low = translate_financial(4.5, 0.03, 800.0, 40.0)
    high = translate_financial(6.5, 0.08, 1600.0, 40.0)
    assert low["interest_rate"] < high["interest_rate"]
    assert low["probability_of_default"] < high["probability_of_default"]
    assert low["insurance_premium"] < high["insurance_premium"]
    # repayment_flexibility depends only on stress, so same for both
    assert low["repayment_flexibility"] == high["repayment_flexibility"]


# ── 6. All dict keys present ─────────────────────────────────────────────────

def test_all_keys_present():
    """All 4 required keys present in output."""
    result = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 50.0)
    assert set(result.keys()) == ALL_KEYS


# ── 7. Negative stress score → clamped to 0 behavior ─────────────────────────

def test_negative_stress_clamped():
    """Negative stress score (shouldn't happen) → same as 0 stress."""
    result_neg = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, -10.0)
    result_zero = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 0.0)
    assert result_neg == result_zero


# ── 8. Insurance premium never below 80% of base ─────────────────────────────

def test_premium_floor_protection():
    """Insurance premium never drops below 80% of base_premium."""
    # Even with zero stress, premium should be >= 0.8 * base
    result = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, 0.0)
    assert result["insurance_premium"] >= BASE_PREMIUM * 0.8

    # With artificially negative stress (clamped to 0), still above floor
    result_neg = translate_financial(BASE_RATE, BASE_PD, BASE_PREMIUM, -50.0)
    assert result_neg["insurance_premium"] >= BASE_PREMIUM * 0.8
