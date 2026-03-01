"""Financial endpoints: financial outputs and old-system vs TerraLend comparison."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.models import Region, FinancialOutput
from backend.models.schemas import FinancialResponse, ComparisonResponse
from backend.services.climate_data import get_climate_data
from backend.services.climate_engine import compute_yield_stress
from backend.services.financial_translator import translate_financial

router = APIRouter()


def _get_region_or_404(region_id: str, db: Session) -> Region:
    region = db.query(Region).filter_by(region_id=region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


async def _compute_terralend_financial(region: Region) -> dict:
    """Compute TerraLend's dynamic financial outputs from current climate data."""
    climate = await get_climate_data(region.region_id, region.lat, region.lng)
    stress = compute_yield_stress(
        climate["temperature_anomaly"],
        climate["drought_index"],
        climate["rainfall_anomaly"],
        climate["ndvi_score"],
        climate["soil_moisture"],
    )
    return translate_financial(
        region.base_loan_rate,
        region.base_pd,
        region.base_premium,
        stress,
    )


@router.get("/region/{region_id}/financial", response_model=FinancialResponse)
async def get_financial(region_id: str, db: Session = Depends(get_db)):
    """Get all financial outputs for a region (TerraLend dynamic values)."""
    region = _get_region_or_404(region_id, db)

    # Get baseline rate from seeded old-system data
    baseline = db.query(FinancialOutput).filter_by(region_id=region_id).first()
    baseline_rate = baseline.baseline_rate if baseline else region.base_loan_rate + 1.5

    # Compute TerraLend dynamic values
    result = await _compute_terralend_financial(region)
    result["baseline_rate"] = baseline_rate
    result["delta_from_baseline"] = round(result["interest_rate"] - baseline_rate, 2)

    return FinancialResponse(**result)


@router.get("/region/{region_id}/comparison", response_model=ComparisonResponse)
async def get_comparison(region_id: str, db: Session = Depends(get_db)):
    """Get old system vs TerraLend side-by-side comparison."""
    region = _get_region_or_404(region_id, db)

    # Old system: static values from seeded baseline (never change)
    baseline = db.query(FinancialOutput).filter_by(region_id=region_id).first()
    old_system = {
        "interest_rate": baseline.interest_rate,
        "probability_of_default": baseline.probability_of_default,
        "insurance_premium": baseline.insurance_premium,
        "repayment_flexibility": baseline.repayment_flexibility,
        "baseline_rate": baseline.baseline_rate,
    }

    # TerraLend: dynamically computed from current climate
    terralend = await _compute_terralend_financial(region)
    terralend["baseline_rate"] = baseline.baseline_rate

    return ComparisonResponse(old_system=old_system, terralend=terralend)
