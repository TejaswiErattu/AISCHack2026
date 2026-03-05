"""
Narrative Service
─────────────────
Generates panel-specific narrative text from a compute_all() bundle.

Panels:
  loan_officer     – risk-focused, mentions PD / rate / dominant stressor
  farmer           – plain-language, actionable advice
  climate_scientist – technical, index-level detail

Two modes (controlled by NARRATIVE_MODE env var):
  "bedrock"  – call Claude 3 Haiku via AWS Bedrock, fall back to templates on error
  "template" – deterministic fallback templates only (default, no AWS needed)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import boto3

# Use Aarul's centralised prompts (Dev3 branch)
from prompts import (
    LOAN_OFFICER_SYSTEM_PROMPT,
    FARMER_SYSTEM_PROMPT,
    CLIMATE_SCIENTIST_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# ── Severity helpers ────────────────────────────────────────────────────

_STRESS_BANDS = [
    (30, "low"),
    (55, "moderate"),
    (75, "elevated"),
    (100, "severe"),
]

_FACTOR_LABELS: Dict[str, str] = {
    "heat":     "heat stress",
    "drought":  "drought conditions",
    "rainfall": "rainfall anomalies",
    "ndvi":     "vegetation decline",
    "soil":     "soil moisture deficit",
}


def _severity(score: float) -> str:
    """Map a 0–100 stress score to a human-readable severity label."""
    for threshold, label in _STRESS_BANDS:
        if score <= threshold:
            return label
    return "severe"


def _pct(val: float) -> str:
    """Format a decimal as a percentage string, e.g. 0.0937 → '9.37%'."""
    return f"{val * 100:.2f}%"


def _signed_pct(val: float) -> str:
    """Format a delta as a signed percentage, e.g. 0.017 → '+1.70%'."""
    return f"{'+' if val >= 0 else ''}{val * 100:.2f}%"


# ── Panel templates ─────────────────────────────────────────────────────

def _loan_officer_narrative(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Risk-focused narrative for a loan officer / underwriter."""
    stress = bundle["stress"]
    fin = bundle["financial"]
    region = bundle["region"]
    score = stress["yield_stress_score"]
    dominant = stress["dominant_factor"]
    sev = _severity(score)

    summary = (
        f"Region {region['region_id']} ({region['name']}) shows "
        f"**{sev}** climate-driven yield risk "
        f"(stress score {score:.1f}/100). "
        f"The dominant factor is {_FACTOR_LABELS.get(dominant, dominant)}, "
        f"contributing {stress['contributions'][dominant]:.1f} points."
    )

    risk_detail = (
        f"Probability of default has moved from "
        f"{_pct(fin['baseline']['pd'])} to {_pct(fin['pd'])} "
        f"({_signed_pct(fin['deltas']['pd'])}). "
        f"Recommended rate: {_pct(fin['interest_rate'])} "
        f"({_signed_pct(fin['deltas']['interest_rate'])} vs baseline). "
        f"Insurance premium: {_pct(fin['insurance_premium'])} "
        f"({_signed_pct(fin['deltas']['insurance_premium'])})."
    )

    recommendation = (
        "Consider tightening collateral requirements."
        if score > 55
        else "Standard underwriting criteria apply."
    )
    if fin["repayment_flexibility_score"] >= 60:
        recommendation += (
            f" Flexibility score of {fin['repayment_flexibility_score']:.0f}/100 "
            f"suggests seasonal repayment scheduling may be appropriate."
        )

    return {
        "panel": "loan_officer",
        "title": f"Underwriting Brief — {region['name']}",
        "sections": [
            {"heading": "Risk Summary", "body": summary},
            {"heading": "Financial Impact", "body": risk_detail},
            {"heading": "Recommendation", "body": recommendation},
        ],
    }


def _farmer_narrative(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Plain-language narrative with actionable advice for a farmer."""
    stress = bundle["stress"]
    fin = bundle["financial"]
    region = bundle["region"]
    climate = bundle["climate"]
    score = stress["yield_stress_score"]
    dominant = stress["dominant_factor"]
    sev = _severity(score)

    overview = (
        f"Your area ({region['name']}) is experiencing **{sev}** "
        f"growing-condition stress right now. "
        f"The biggest concern is {_FACTOR_LABELS.get(dominant, dominant)}."
    )

    conditions = []
    if climate.get("temperature_anomaly_c", 0) > 1.5:
        conditions.append(
            f"Temperatures are running {climate['temperature_anomaly_c']:.1f}°C "
            f"above normal — watch for heat damage to {region['primary_crop']}."
        )
    if climate.get("drought_index", 0) > 60:
        conditions.append(
            f"Drought index is at {climate['drought_index']:.0f}/100 — "
            f"irrigation planning is critical."
        )
    if climate.get("soil_moisture", 100) < 35:
        conditions.append(
            f"Soil moisture is low ({climate['soil_moisture']:.0f}%). "
            f"Consider cover-cropping or mulching to retain moisture."
        )
    if not conditions:
        conditions.append(
            "Current climate conditions are within normal ranges for your area."
        )

    loan_impact = (
        f"Based on current conditions, your loan rate would be around "
        f"{_pct(fin['interest_rate'])} "
        f"(baseline is {_pct(fin['baseline']['interest_rate'])}). "
    )
    if fin["repayment_flexibility_score"] >= 50:
        loan_impact += (
            "You may qualify for seasonal repayment flexibility — "
            "ask your loan officer about adjusted payment schedules."
        )

    return {
        "panel": "farmer",
        "title": f"Your Field Report — {region['name']}",
        "sections": [
            {"heading": "Overview", "body": overview},
            {"heading": "What to Watch", "body": " ".join(conditions)},
            {"heading": "What This Means for Your Loan", "body": loan_impact},
        ],
    }


def _climate_scientist_narrative(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Technical narrative with index-level detail for a climate analyst."""
    stress = bundle["stress"]
    indices = bundle["normalized_indices"]
    climate = bundle["climate"]
    region = bundle["region"]
    score = stress["yield_stress_score"]
    weights = stress["weights_used"]

    index_lines = []
    for key, val in indices.items():
        index_lines.append(f"  • {key}: {val:.1f}/100")
    index_block = "\n".join(index_lines)

    raw_lines = [
        f"  • Temperature anomaly: {climate.get('temperature_anomaly_c', 'N/A')}°C",
        f"  • Drought index: {climate.get('drought_index', 'N/A')}",
        f"  • Rainfall anomaly: {climate.get('rainfall_anomaly_pct', 'N/A')}%",
        f"  • NDVI score: {climate.get('ndvi_score', 'N/A')}",
        f"  • Soil moisture: {climate.get('soil_moisture', 'N/A')}%",
    ]
    raw_block = "\n".join(raw_lines)

    contrib_lines = []
    for factor, contrib in stress["contributions"].items():
        w = weights.get(factor, 0)
        contrib_lines.append(
            f"  • {factor}: {contrib:.2f} pts (weight {w:.2f})"
        )
    contrib_block = "\n".join(contrib_lines)

    methodology = (
        f"Composite yield stress score: **{score:.2f}** / 100\n"
        f"Weighted linear combination of normalised indices.\n\n"
        f"Contributions:\n{contrib_block}\n\n"
        f"Data source: {climate.get('source', 'unknown')}"
    )

    return {
        "panel": "climate_scientist",
        "title": f"Climate Risk Analysis — {region['name']} ({region['region_id']})",
        "sections": [
            {"heading": "Raw Observations", "body": raw_block},
            {"heading": "Normalised Stress Indices", "body": index_block},
            {"heading": "Methodology & Scoring", "body": methodology},
        ],
    }


# ── Public API ──────────────────────────────────────────────────────────

_PANELS = {
    "loan_officer": _loan_officer_narrative,
    "farmer": _farmer_narrative,
    "climate_scientist": _climate_scientist_narrative,
}

VALID_PANELS = list(_PANELS.keys())

# ── Bedrock / LLM narrative ────────────────────────────────────────────

_BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

_PANEL_SYSTEM_PROMPTS: Dict[str, str] = {
    "loan_officer": LOAN_OFFICER_SYSTEM_PROMPT,
    "farmer": FARMER_SYSTEM_PROMPT,
    "climate_scientist": CLIMATE_SCIENTIST_SYSTEM_PROMPT,
}


def _build_bedrock_user_message(panel: str, bundle: Dict[str, Any]) -> str:
    """Build a structured user message with all data for the LLM."""
    region = bundle["region"]
    climate = bundle["climate"]
    indices = bundle["normalized_indices"]
    stress = bundle["stress"]
    fin = bundle["financial"]

    return json.dumps({
        "region": {
            "id": region["region_id"],
            "name": region["name"],
            "crop": region["primary_crop"],
            "lat": region["lat"],
            "lng": region["lng"],
        },
        "climate_snapshot": {
            "temperature_anomaly_c": climate.get("temperature_anomaly_c"),
            "drought_index": climate.get("drought_index"),
            "rainfall_anomaly_pct": climate.get("rainfall_anomaly_pct"),
            "ndvi_score": climate.get("ndvi_score"),
            "soil_moisture": climate.get("soil_moisture"),
            "source": climate.get("source"),
        },
        "normalized_indices": indices,
        "stress": {
            "yield_stress_score": stress["yield_stress_score"],
            "dominant_factor": stress["dominant_factor"],
            "contributions": stress["contributions"],
            "weights": stress["weights_used"],
        },
        "financial": {
            "pd": fin["pd"],
            "interest_rate": fin["interest_rate"],
            "insurance_premium": fin["insurance_premium"],
            "repayment_flexibility_score": fin["repayment_flexibility_score"],
            "baseline_pd": fin["baseline"]["pd"],
            "baseline_rate": fin["baseline"]["interest_rate"],
            "baseline_premium": fin["baseline"]["insurance_premium"],
            "deltas": fin["deltas"],
        },
    }, indent=2)


def _call_bedrock(panel: str, bundle: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Call Claude 3 Haiku via Bedrock Converse API.
    Returns narrative dict on success, None on any failure.
    """
    try:
        region = bundle["region"]
        client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-west-2"),
        )

        system_prompt = _PANEL_SYSTEM_PROMPTS[panel]
        user_msg = _build_bedrock_user_message(panel, bundle)

        response = client.converse(
            modelId=_BEDROCK_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": f"Generate a {panel} narrative for this agricultural region data:\n\n{user_msg}"}
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.3,
            },
        )

        # Extract text from Converse response
        text = response["output"]["message"]["content"][0]["text"]

        # Parse into sections (LLM is prompted for 3 paragraphs)
        template = _PANELS[panel](bundle)  # get headings from template
        headings = [s["heading"] for s in template["sections"]]

        # Split LLM text into paragraphs and map to headings
        paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]

        sections = []
        for i, heading in enumerate(headings):
            body = paragraphs[i] if i < len(paragraphs) else template["sections"][i]["body"]
            sections.append({"heading": heading, "body": body})

        return {
            "panel": panel,
            "title": template["title"],
            "sections": sections,
            "source": "bedrock",
            "model": _BEDROCK_MODEL_ID,
        }

    except Exception as e:
        logger.warning("Bedrock narrative failed for panel=%s: %s", panel, e)
        return None


def generate_narrative(
    panel: str,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a panel-specific narrative from a compute_all() bundle.

    If NARRATIVE_MODE=bedrock, tries Claude via Bedrock first and falls
    back to deterministic templates on any error.

    Parameters
    ----------
    panel : str
        One of 'loan_officer', 'farmer', 'climate_scientist'.
    bundle : dict
        Full output of compute_all().

    Returns
    -------
    dict with keys: panel, title, sections[], source
    """
    handler = _PANELS.get(panel)
    if handler is None:
        return {
            "error": f"Unknown panel '{panel}'. Valid panels: {VALID_PANELS}",
            "valid_panels": VALID_PANELS,
        }

    # Try Bedrock if enabled
    mode = os.getenv("NARRATIVE_MODE", "template").lower()
    if mode == "bedrock":
        result = _call_bedrock(panel, bundle)
        if result is not None:
            return result
        logger.info("Falling back to template for panel=%s", panel)

    # Fallback: deterministic template
    result = handler(bundle)
    result["source"] = "template"
    return result
