"""Region endpoints: list regions, get climate data, get stress score."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.models import Region
from backend.models.schemas import RegionResponse, ClimateResponse, StressResponse
from backend.services.climate_data import get_climate_data
from backend.services.climate_engine import compute_yield_stress, compute_stress_breakdown

router = APIRouter()


def _get_region_or_404(region_id: str, db: Session) -> Region:
    """Look up a region by ID, raise 404 if not found."""
    region = db.query(Region).filter_by(region_id=region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.get("/regions", response_model=list[RegionResponse])
async def list_regions(db: Session = Depends(get_db)):
    """List all selectable US agricultural regions with computed stress scores."""
    regions = db.query(Region).all()
    result = []
    for region in regions:
        climate = await get_climate_data(region.region_id, region.lat, region.lng)
        stress = compute_yield_stress(
            climate["temperature_anomaly"],
            climate["drought_index"],
            climate["rainfall_anomaly"],
            climate["ndvi_score"],
            climate["soil_moisture"],
        )
        result.append(RegionResponse(
            region_id=region.region_id,
            name=region.name,
            lat=region.lat,
            lng=region.lng,
            primary_crop=region.primary_crop,
            stress_score=stress,
        ))
    return result


@router.get("/region/{region_id}/climate", response_model=ClimateResponse)
async def get_region_climate(region_id: str, db: Session = Depends(get_db)):
    """Get current climate data for a region."""
    region = _get_region_or_404(region_id, db)
    climate = await get_climate_data(region_id, region.lat, region.lng)
    stress = compute_yield_stress(
        climate["temperature_anomaly"],
        climate["drought_index"],
        climate["rainfall_anomaly"],
        climate["ndvi_score"],
        climate["soil_moisture"],
    )
    return ClimateResponse(**climate, yield_stress_score=stress)


@router.get("/region/{region_id}/stress", response_model=StressResponse)
async def get_region_stress(region_id: str, db: Session = Depends(get_db)):
    """Get yield stress score and factor breakdown for a region."""
    region = _get_region_or_404(region_id, db)
    climate = await get_climate_data(region_id, region.lat, region.lng)

    stress = compute_yield_stress(
        climate["temperature_anomaly"],
        climate["drought_index"],
        climate["rainfall_anomaly"],
        climate["ndvi_score"],
        climate["soil_moisture"],
    )
    breakdown = compute_stress_breakdown(
        climate["temperature_anomaly"],
        climate["drought_index"],
        climate["rainfall_anomaly"],
        climate["ndvi_score"],
        climate["soil_moisture"],
    )

    return StressResponse(yield_stress_score=stress, breakdown=breakdown)
