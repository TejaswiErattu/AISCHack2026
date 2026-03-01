"""Simulation endpoints: single climate shock and batch archetype simulation."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.models import Region, FinancialOutput
from backend.models.schemas import SimulateRequest, SimulateResponse, FinancialResponse
from backend.services.climate_data import get_climate_data
from backend.services.climate_engine import compute_yield_stress
from backend.services.financial_translator import translate_financial

router = APIRouter()

# Batch simulation presets matching frontend MOCK_SIMULATION shape
BATCH_SCENARIOS = [
    {"name": "Dust Bowl Echo", "icon": "🌵", "color": "#EF4444", "temperature_delta": 4, "drought_index": 90, "rainfall_anomaly": -70},
    {"name": "The Deluge", "icon": "🌊", "color": "#3B82F6", "temperature_delta": -1, "drought_index": 5, "rainfall_anomaly": 70},
    {"name": "Late Frost", "icon": "🌨️", "color": "#8B5CF6", "temperature_delta": -3, "drought_index": 20, "rainfall_anomaly": -20},
    {"name": "Baseline", "icon": "📊", "color": "#10B981", "temperature_delta": 0, "drought_index": None, "rainfall_anomaly": None},
]


class BatchSimulateRequest(BaseModel):
    region_id: str


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: SimulateRequest, db: Session = Depends(get_db)):
    """Simulate climate shock: merge overrides with current data, recompute everything."""
    region = db.query(Region).filter_by(region_id=req.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # Get current climate data (baseline)
    climate = await get_climate_data(region.region_id, region.lat, region.lng)

    # Compute baseline stress + financial
    baseline_stress = compute_yield_stress(
        climate["temperature_anomaly"],
        climate["drought_index"],
        climate["rainfall_anomaly"],
        climate["ndvi_score"],
        climate["soil_moisture"],
    )
    baseline_financial = translate_financial(
        region.base_loan_rate, region.base_pd, region.base_premium, baseline_stress,
    )

    # Get old-system baseline rate
    baseline_row = db.query(FinancialOutput).filter_by(region_id=req.region_id).first()
    old_system_rate = baseline_row.baseline_rate if baseline_row else region.base_loan_rate + 1.5

    # Apply overrides to climate data
    sim_climate = dict(climate)
    if req.temperature_delta is not None:
        sim_climate["temperature_anomaly"] += req.temperature_delta  # additive
    if req.drought_index is not None:
        sim_climate["drought_index"] = req.drought_index  # replacement
    if req.rainfall_anomaly is not None:
        sim_climate["rainfall_anomaly"] = req.rainfall_anomaly  # replacement
    if req.ndvi_score is not None:
        sim_climate["ndvi_score"] = req.ndvi_score  # replacement
    if req.soil_moisture is not None:
        sim_climate["soil_moisture"] = req.soil_moisture  # replacement

    # Compute simulated stress + financial
    sim_stress = compute_yield_stress(
        sim_climate["temperature_anomaly"],
        sim_climate["drought_index"],
        sim_climate["rainfall_anomaly"],
        sim_climate["ndvi_score"],
        sim_climate["soil_moisture"],
    )
    sim_financial = translate_financial(
        region.base_loan_rate, region.base_pd, region.base_premium, sim_stress,
    )

    # Compute deltas (simulated - baseline)
    deltas = {
        "stress_score": round(sim_stress - baseline_stress, 2),
        "interest_rate": round(sim_financial["interest_rate"] - baseline_financial["interest_rate"], 2),
        "probability_of_default": round(sim_financial["probability_of_default"] - baseline_financial["probability_of_default"], 4),
        "insurance_premium": round(sim_financial["insurance_premium"] - baseline_financial["insurance_premium"], 2),
        "repayment_flexibility": round(sim_financial["repayment_flexibility"] - baseline_financial["repayment_flexibility"], 2),
    }

    baseline_financial["baseline_rate"] = old_system_rate
    baseline_financial["delta_from_baseline"] = round(baseline_financial["interest_rate"] - old_system_rate, 2)
    sim_financial["baseline_rate"] = old_system_rate
    sim_financial["delta_from_baseline"] = round(sim_financial["interest_rate"] - old_system_rate, 2)

    return SimulateResponse(
        region_id=req.region_id,
        baseline=FinancialResponse(**baseline_financial),
        simulated=FinancialResponse(**sim_financial),
        stress_score=sim_stress,
        baseline_stress=baseline_stress,
        deltas=deltas,
    )


@router.post("/simulate/batch")
async def simulate_batch(req: BatchSimulateRequest, db: Session = Depends(get_db)):
    """Run 4 preset climate scenarios and return results matching MOCK_SIMULATION shape."""
    region = db.query(Region).filter_by(region_id=req.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    climate = await get_climate_data(region.region_id, region.lat, region.lng)
    results = []

    for scenario in BATCH_SCENARIOS:
        sim_climate = dict(climate)
        # Apply scenario overrides
        if scenario["temperature_delta"] is not None:
            sim_climate["temperature_anomaly"] += scenario["temperature_delta"]
        if scenario["drought_index"] is not None:
            sim_climate["drought_index"] = scenario["drought_index"]
        if scenario["rainfall_anomaly"] is not None:
            sim_climate["rainfall_anomaly"] = scenario["rainfall_anomaly"]

        stress = compute_yield_stress(
            sim_climate["temperature_anomaly"],
            sim_climate["drought_index"],
            sim_climate["rainfall_anomaly"],
            sim_climate["ndvi_score"],
            sim_climate["soil_moisture"],
        )
        financial = translate_financial(
            region.base_loan_rate, region.base_pd, region.base_premium, stress,
        )

        results.append({
            "name": scenario["name"],
            "icon": scenario["icon"],
            "color": scenario["color"],
            "stress_score": round(stress, 1),
            "interest_rate": financial["interest_rate"],
            "pd": financial["probability_of_default"],
        })

    return results
