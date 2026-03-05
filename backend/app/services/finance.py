"""
Financial Risk Translator
─────────────────────────
Converts a Yield Stress Score (0–100) + region baseline into
loan-level financial outputs: PD, interest rate, insurance premium,
and repayment flexibility.

Also returns deltas vs baseline for the frontend "↑ +0.9% rate" indicators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class RegionBase:
    """Baseline financial parameters for a region (from SQLite)."""
    base_loan_rate: float   # e.g. 0.075 for 7.5%
    base_pd: float          # e.g. 0.030 for 3.0%
    base_premium: float     # e.g. 0.012 for 1.2%


def compute_financial(
    region: RegionBase,
    yield_stress_score: float,
    *,
    # Tunable parameters (PRD defaults)
    stress_multiplier: float = 0.15,
    rate_sensitivity: float = 0.04,
    pd_floor: float = 0.01,
    pd_ceiling: float = 0.20,
    rate_floor: float = 0.02,
    rate_ceiling: float = 0.25,
    premium_stress_factor: float = 1.5,
) -> Dict[str, Any]:
    """
    Translate climate-driven yield stress into financial risk outputs.

    Parameters
    ----------
    region : RegionBase
        Baseline loan parameters from the region config store.
    yield_stress_score : float
        0–100 from the Yield Stress Engine.

    Returns
    -------
    dict with:
        pd, interest_rate, insurance_premium,
        repayment_flexibility_score, deltas, debug
    """
    # 1) Normalize stress to 0–1
    stress_norm = _clamp(yield_stress_score / 100.0, 0.0, 1.0)

    # 2) Probability of Default
    #    PD = base_pd + multiplier × stress
    pd = region.base_pd + (stress_multiplier * stress_norm)
    pd = round(_clamp(pd, pd_floor, pd_ceiling), 4)

    # 3) Interest Rate
    #    rate = base_rate + rate_sensitivity × stress
    #    (direct stress-driven; avoids compounding with PD)
    interest_rate = region.base_loan_rate + (rate_sensitivity * stress_norm)
    interest_rate = round(_clamp(interest_rate, rate_floor, rate_ceiling), 4)

    # 4) Insurance Premium
    #    premium = base + base × factor × stress
    insurance_premium = region.base_premium + (
        region.base_premium * premium_stress_factor * stress_norm
    )
    insurance_premium = round(insurance_premium, 4)

    # 5) Repayment Flexibility Score (0–100)
    #    Higher stress → more flexibility offered (bank accommodates risk)
    #    Low stress → 20 (standard terms), high stress → 100 (max flexibility)
    repayment_flexibility_score = round(
        _clamp(20 + 80 * stress_norm, 0, 100), 1
    )

    # 6) Deltas vs baseline (for "↑ +0.9%" UI indicators)
    rate_delta = round(interest_rate - region.base_loan_rate, 4)
    pd_delta_final = round(pd - region.base_pd, 4)
    premium_delta = round(insurance_premium - region.base_premium, 4)

    return {
        "pd": pd,
        "interest_rate": interest_rate,
        "insurance_premium": insurance_premium,
        "repayment_flexibility_score": repayment_flexibility_score,
        "deltas": {
            "pd": pd_delta_final,
            "interest_rate": rate_delta,
            "insurance_premium": premium_delta,
        },
        "baseline": {
            "pd": region.base_pd,
            "interest_rate": region.base_loan_rate,
            "insurance_premium": region.base_premium,
        },
        "debug": {
            "stress_norm": round(stress_norm, 4),
            "yield_stress_score": yield_stress_score,
        },
    }
