"""Financial Risk Translator.

Converts yield stress score into financial outputs: interest rate,
probability of default, insurance premium, and repayment flexibility.

Deterministic formulas from PRD Section 4.4.
"""


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def translate_financial(
    base_rate: float,
    base_pd: float,
    base_premium: float,
    yield_stress_score: float,
) -> dict:
    """Translate yield stress score into financial outputs.

    Args:
        base_rate: Region's base loan interest rate (e.g., 5.5%)
        base_pd: Region's base probability of default (e.g., 0.05)
        base_premium: Region's base insurance premium (e.g., $1200)
        yield_stress_score: 0–100 stress score from climate engine

    Returns:
        Dict with keys: interest_rate, probability_of_default,
        insurance_premium, repayment_flexibility
    """
    # Defensive: clamp stress to valid range
    stress = _clamp(yield_stress_score, 0, 100)

    # 1. Probability of default
    pd = base_pd + (stress / 100) * 0.25
    pd = _clamp(pd, 0.01, 0.50)

    # 2. Interest rate (depends on PD)
    interest_rate = base_rate + (pd * 0.08 * 100)
    interest_rate = _clamp(interest_rate, 3.0, 15.0)

    # 3. Insurance premium
    insurance_premium = base_premium * (1 + stress / 100)
    insurance_premium = _clamp(insurance_premium, base_premium * 0.8, base_premium * 3.0)

    # 4. Repayment flexibility (inverse of stress)
    repayment_flexibility = _clamp(100 - stress, 0, 100)

    return {
        "interest_rate": round(interest_rate, 2),
        "probability_of_default": round(pd, 4),
        "insurance_premium": round(insurance_premium, 2),
        "repayment_flexibility": round(repayment_flexibility, 2),
    }
