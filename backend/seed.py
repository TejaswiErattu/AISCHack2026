"""Seed script: populates 20 US agricultural regions with realistic baseline data.

Idempotent — safe to run multiple times without creating duplicates.
"""
import uuid
from sqlalchemy.orm import Session

from backend.models.database import SessionLocal, create_tables
from backend.models.models import Region, ClimateSnapshot, FinancialOutput


# ── 20 US Agricultural Regions ──────────────────────────────────────────────
# Each has real coordinates, appropriate crop, and realistic base financials.
# base_loan_rate: 4.5–6.5%  |  base_pd: 0.03–0.08  |  base_premium: 800–1600

REGIONS = [
    {"region_id": "central-valley-ca",    "name": "Central Valley, CA",      "lat": 36.75, "lng": -119.77, "primary_crop": "almonds",    "base_loan_rate": 5.5, "base_pd": 0.05, "base_premium": 1200},
    {"region_id": "midwest-corn-belt-ia", "name": "Midwest Corn Belt, IA",   "lat": 42.03, "lng": -93.47,  "primary_crop": "corn",       "base_loan_rate": 5.0, "base_pd": 0.04, "base_premium": 1000},
    {"region_id": "texas-panhandle-tx",   "name": "Texas Panhandle, TX",     "lat": 35.20, "lng": -101.83, "primary_crop": "cotton",     "base_loan_rate": 6.0, "base_pd": 0.07, "base_premium": 1400},
    {"region_id": "columbia-basin-wa",    "name": "Columbia Basin, WA",      "lat": 46.80, "lng": -119.30, "primary_crop": "potatoes",   "base_loan_rate": 5.2, "base_pd": 0.04, "base_premium": 1050},
    {"region_id": "mississippi-delta-ms", "name": "Mississippi Delta, MS",   "lat": 33.40, "lng": -90.90,  "primary_crop": "soybeans",   "base_loan_rate": 5.8, "base_pd": 0.06, "base_premium": 1300},
    {"region_id": "san-joaquin-valley-ca","name": "San Joaquin Valley, CA",  "lat": 36.33, "lng": -119.64, "primary_crop": "grapes",     "base_loan_rate": 5.6, "base_pd": 0.05, "base_premium": 1250},
    {"region_id": "nebraska-sandhills-ne","name": "Nebraska Sandhills, NE",  "lat": 42.10, "lng": -101.20, "primary_crop": "cattle/hay", "base_loan_rate": 5.3, "base_pd": 0.05, "base_premium": 1100},
    {"region_id": "kansas-wheat-belt-ks", "name": "Kansas Wheat Belt, KS",   "lat": 38.50, "lng": -98.75,  "primary_crop": "wheat",      "base_loan_rate": 5.1, "base_pd": 0.04, "base_premium": 1000},
    {"region_id": "sacramento-valley-ca", "name": "Sacramento Valley, CA",   "lat": 39.15, "lng": -121.69, "primary_crop": "rice",       "base_loan_rate": 5.4, "base_pd": 0.05, "base_premium": 1150},
    {"region_id": "florida-citrus-belt-fl","name": "Florida Citrus Belt, FL","lat": 28.10, "lng": -81.60,  "primary_crop": "citrus",     "base_loan_rate": 5.7, "base_pd": 0.06, "base_premium": 1350},
    {"region_id": "willamette-valley-or", "name": "Willamette Valley, OR",   "lat": 44.75, "lng": -123.07, "primary_crop": "berries",    "base_loan_rate": 4.8, "base_pd": 0.03, "base_premium": 900},
    {"region_id": "red-river-valley-nd",  "name": "Red River Valley, ND",    "lat": 47.90, "lng": -97.03,  "primary_crop": "sugar beets","base_loan_rate": 5.0, "base_pd": 0.04, "base_premium": 1050},
    {"region_id": "yakima-valley-wa",     "name": "Yakima Valley, WA",       "lat": 46.60, "lng": -120.50, "primary_crop": "apples",     "base_loan_rate": 4.9, "base_pd": 0.04, "base_premium": 950},
    {"region_id": "imperial-valley-ca",   "name": "Imperial Valley, CA",     "lat": 32.85, "lng": -115.57, "primary_crop": "lettuce",    "base_loan_rate": 6.2, "base_pd": 0.07, "base_premium": 1500},
    {"region_id": "snake-river-plain-id", "name": "Snake River Plain, ID",   "lat": 42.87, "lng": -114.46, "primary_crop": "potatoes",   "base_loan_rate": 5.0, "base_pd": 0.04, "base_premium": 1000},
    {"region_id": "ozark-plateau-mo",     "name": "Ozark Plateau, MO",       "lat": 37.20, "lng": -92.50,  "primary_crop": "cattle/hay", "base_loan_rate": 5.4, "base_pd": 0.05, "base_premium": 1100},
    {"region_id": "bluegrass-region-ky",  "name": "Bluegrass Region, KY",    "lat": 38.05, "lng": -84.50,  "primary_crop": "tobacco",    "base_loan_rate": 5.3, "base_pd": 0.05, "base_premium": 1100},
    {"region_id": "palouse-wa",           "name": "Palouse, WA",             "lat": 46.73, "lng": -117.17, "primary_crop": "wheat",      "base_loan_rate": 4.7, "base_pd": 0.03, "base_premium": 850},
    {"region_id": "rio-grande-valley-tx", "name": "Rio Grande Valley, TX",   "lat": 26.20, "lng": -98.23,  "primary_crop": "citrus",     "base_loan_rate": 6.5, "base_pd": 0.08, "base_premium": 1600},
    {"region_id": "shenandoah-valley-va", "name": "Shenandoah Valley, VA",   "lat": 38.15, "lng": -79.07,  "primary_crop": "apples",     "base_loan_rate": 4.5, "base_pd": 0.03, "base_premium": 800},
]


# ── Baseline Climate Snapshots ──────────────────────────────────────────────
# Seasonal-norm values per region. Hotter/drier regions get higher anomalies.
# All values within valid ranges: temp_anomaly (-5..+8), drought (0..100),
# rainfall_anomaly (-80..+80), ndvi (0..100), soil_moisture (0..100).

BASELINE_CLIMATE = {
    "central-valley-ca":     {"temperature_anomaly": 1.2, "drought_index": 45, "rainfall_anomaly": -15, "ndvi_score": 62, "soil_moisture": 40},
    "midwest-corn-belt-ia":  {"temperature_anomaly": 0.5, "drought_index": 20, "rainfall_anomaly": 5,   "ndvi_score": 78, "soil_moisture": 65},
    "texas-panhandle-tx":    {"temperature_anomaly": 2.0, "drought_index": 55, "rainfall_anomaly": -25, "ndvi_score": 50, "soil_moisture": 35},
    "columbia-basin-wa":     {"temperature_anomaly": 0.3, "drought_index": 25, "rainfall_anomaly": -5,  "ndvi_score": 72, "soil_moisture": 58},
    "mississippi-delta-ms":  {"temperature_anomaly": 1.0, "drought_index": 30, "rainfall_anomaly": 10,  "ndvi_score": 70, "soil_moisture": 60},
    "san-joaquin-valley-ca": {"temperature_anomaly": 1.5, "drought_index": 50, "rainfall_anomaly": -20, "ndvi_score": 58, "soil_moisture": 38},
    "nebraska-sandhills-ne": {"temperature_anomaly": 0.8, "drought_index": 35, "rainfall_anomaly": -10, "ndvi_score": 65, "soil_moisture": 50},
    "kansas-wheat-belt-ks":  {"temperature_anomaly": 0.7, "drought_index": 30, "rainfall_anomaly": -8,  "ndvi_score": 70, "soil_moisture": 55},
    "sacramento-valley-ca":  {"temperature_anomaly": 1.0, "drought_index": 40, "rainfall_anomaly": -12, "ndvi_score": 65, "soil_moisture": 45},
    "florida-citrus-belt-fl":{"temperature_anomaly": 0.8, "drought_index": 25, "rainfall_anomaly": 15,  "ndvi_score": 75, "soil_moisture": 70},
    "willamette-valley-or":  {"temperature_anomaly": 0.2, "drought_index": 15, "rainfall_anomaly": 8,   "ndvi_score": 82, "soil_moisture": 72},
    "red-river-valley-nd":   {"temperature_anomaly": 0.4, "drought_index": 22, "rainfall_anomaly": 3,   "ndvi_score": 75, "soil_moisture": 62},
    "yakima-valley-wa":      {"temperature_anomaly": 0.3, "drought_index": 20, "rainfall_anomaly": -3,  "ndvi_score": 76, "soil_moisture": 60},
    "imperial-valley-ca":    {"temperature_anomaly": 2.5, "drought_index": 65, "rainfall_anomaly": -35, "ndvi_score": 45, "soil_moisture": 28},
    "snake-river-plain-id":  {"temperature_anomaly": 0.4, "drought_index": 25, "rainfall_anomaly": -5,  "ndvi_score": 70, "soil_moisture": 55},
    "ozark-plateau-mo":      {"temperature_anomaly": 0.6, "drought_index": 20, "rainfall_anomaly": 5,   "ndvi_score": 74, "soil_moisture": 62},
    "bluegrass-region-ky":   {"temperature_anomaly": 0.5, "drought_index": 18, "rainfall_anomaly": 3,   "ndvi_score": 76, "soil_moisture": 65},
    "palouse-wa":            {"temperature_anomaly": 0.2, "drought_index": 18, "rainfall_anomaly": -2,  "ndvi_score": 78, "soil_moisture": 63},
    "rio-grande-valley-tx":  {"temperature_anomaly": 2.2, "drought_index": 60, "rainfall_anomaly": -30, "ndvi_score": 48, "soil_moisture": 30},
    "shenandoah-valley-va":  {"temperature_anomaly": 0.3, "drought_index": 15, "rainfall_anomaly": 5,   "ndvi_score": 80, "soil_moisture": 68},
}


def _compute_baseline_stress(climate: dict) -> float:
    """Compute yield stress score using the PRD formula (Section 4.3).

    This duplicates the formula we'll formalize in Task 3.1, but we need it here
    to pre-populate baseline snapshots with their stress scores.
    """
    temp = climate["temperature_anomaly"]
    heat_stress = max(0.0, min(100.0, (temp + 3) / 8 * 100))
    drought = climate["drought_index"]
    rain = climate["rainfall_anomaly"]
    rainfall_stress = min(100.0, abs(rain) / 80 * 100)
    ndvi_deficit = 100 - climate["ndvi_score"]
    soil_deficit = 100 - climate["soil_moisture"]

    stress = (
        0.30 * heat_stress
        + 0.25 * drought
        + 0.20 * rainfall_stress
        + 0.15 * ndvi_deficit
        + 0.10 * soil_deficit
    )
    return max(0.0, min(100.0, round(stress, 2)))


def seed_database(db: Session) -> None:
    """Seed all regions, baseline climate snapshots, and baseline financial outputs.

    Idempotent: skips regions that already exist.
    """
    for region_data in REGIONS:
        rid = region_data["region_id"]

        # Skip if region already exists
        existing = db.query(Region).filter_by(region_id=rid).first()
        if existing:
            continue

        # 1. Insert Region
        region = Region(**region_data)
        db.add(region)
        db.flush()  # ensure region_id is available for FK

        # 2. Insert baseline ClimateSnapshot
        climate = BASELINE_CLIMATE[rid]
        stress = _compute_baseline_stress(climate)
        snapshot_id = f"baseline-{rid}"
        snapshot = ClimateSnapshot(
            snapshot_id=snapshot_id,
            region_id=rid,
            temperature_anomaly=climate["temperature_anomaly"],
            drought_index=climate["drought_index"],
            rainfall_anomaly=climate["rainfall_anomaly"],
            ndvi_score=climate["ndvi_score"],
            soil_moisture=climate["soil_moisture"],
            yield_stress_score=stress,
        )
        db.add(snapshot)
        db.flush()

        # 3. Insert baseline FinancialOutput ("old system" static rate)
        # Old system adds a static 1.0–2.0% markup based on region risk tier
        # Linearly map base_pd (0.03–0.08) → markup (1.0–2.0)
        static_markup = 1.0 + (region_data["base_pd"] - 0.03) / 0.05 * 1.0
        old_system_rate = region_data["base_loan_rate"] + static_markup
        output = FinancialOutput(
            output_id=f"baseline-{rid}",
            region_id=rid,
            snapshot_id=snapshot_id,
            interest_rate=old_system_rate,
            probability_of_default=region_data["base_pd"],
            insurance_premium=region_data["base_premium"],
            repayment_flexibility=100.0,  # old system doesn't flex
            baseline_rate=old_system_rate,
        )
        db.add(output)

    db.commit()


def run_seed():
    """Entry point: create tables and seed data."""
    create_tables()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
    print("Seed complete.")
