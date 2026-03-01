"""Tests for Task 1.3: Seed data script."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base
from backend.models.models import Region, ClimateSnapshot, FinancialOutput
from backend.seed import seed_database, REGIONS, BASELINE_CLIMATE


@pytest.fixture
def db_session():
    """Fresh in-memory DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_seed_creates_all_regions(db_session):
    """All 20+ regions present after seeding."""
    seed_database(db_session)
    count = db_session.query(Region).count()
    assert count >= 20


def test_seed_idempotent(db_session):
    """Running seed twice does not create duplicates."""
    seed_database(db_session)
    count_first = db_session.query(Region).count()
    seed_database(db_session)
    count_second = db_session.query(Region).count()
    assert count_first == count_second


def test_region_coordinates_valid(db_session):
    """All regions have valid lat (-90..90) and lng (-180..180)."""
    seed_database(db_session)
    regions = db_session.query(Region).all()
    for r in regions:
        assert -90 <= r.lat <= 90, f"{r.region_id} lat {r.lat} out of range"
        assert -180 <= r.lng <= 180, f"{r.region_id} lng {r.lng} out of range"


def test_base_financial_values_realistic(db_session):
    """base_loan_rate 4.5–6.5%, base_pd 0.03–0.08, base_premium 800–1600."""
    seed_database(db_session)
    regions = db_session.query(Region).all()
    for r in regions:
        assert 4.5 <= r.base_loan_rate <= 6.5, f"{r.region_id} rate {r.base_loan_rate}"
        assert 0.03 <= r.base_pd <= 0.08, f"{r.region_id} pd {r.base_pd}"
        assert 800 <= r.base_premium <= 1600, f"{r.region_id} premium {r.base_premium}"


def test_baseline_climate_no_zeros_no_extremes(db_session):
    """Baseline climate snapshots have reasonable seasonal values."""
    seed_database(db_session)
    snapshots = db_session.query(ClimateSnapshot).all()
    for s in snapshots:
        # No zeros across the board (at least some fields should be nonzero)
        values = [s.temperature_anomaly, s.drought_index, s.rainfall_anomaly, s.ndvi_score, s.soil_moisture]
        assert any(v != 0 for v in values), f"{s.region_id} all zeros"
        # Within valid ranges
        assert -5 <= s.temperature_anomaly <= 8, f"{s.region_id} temp {s.temperature_anomaly}"
        assert 0 <= s.drought_index <= 100, f"{s.region_id} drought {s.drought_index}"
        assert -80 <= s.rainfall_anomaly <= 80, f"{s.region_id} rain {s.rainfall_anomaly}"
        assert 0 <= s.ndvi_score <= 100, f"{s.region_id} ndvi {s.ndvi_score}"
        assert 0 <= s.soil_moisture <= 100, f"{s.region_id} soil {s.soil_moisture}"


def test_each_region_has_one_snapshot_and_one_output(db_session):
    """Each region has exactly one baseline ClimateSnapshot and one baseline FinancialOutput."""
    seed_database(db_session)
    regions = db_session.query(Region).all()
    for r in regions:
        snap_count = db_session.query(ClimateSnapshot).filter_by(region_id=r.region_id).count()
        assert snap_count == 1, f"{r.region_id} has {snap_count} snapshots"
        fin_count = db_session.query(FinancialOutput).filter_by(region_id=r.region_id).count()
        assert fin_count == 1, f"{r.region_id} has {fin_count} financial outputs"


def test_old_system_rate_above_base(db_session):
    """Old system baseline rate is base_loan_rate + 1.0 to 2.0."""
    seed_database(db_session)
    regions = db_session.query(Region).all()
    for r in regions:
        fo = db_session.query(FinancialOutput).filter_by(region_id=r.region_id).first()
        markup = fo.baseline_rate - r.base_loan_rate
        assert 1.0 <= markup <= 2.0, f"{r.region_id} markup {markup}"


def test_stress_scores_within_range(db_session):
    """All baseline yield_stress_scores are 0–100."""
    seed_database(db_session)
    snapshots = db_session.query(ClimateSnapshot).all()
    for s in snapshots:
        assert 0 <= s.yield_stress_score <= 100, f"{s.region_id} stress {s.yield_stress_score}"


def test_climate_varies_by_region(db_session):
    """Different regions have different climate values (not all identical)."""
    seed_database(db_session)
    snapshots = db_session.query(ClimateSnapshot).all()
    temps = {s.temperature_anomaly for s in snapshots}
    droughts = {s.drought_index for s in snapshots}
    assert len(temps) > 5, "Too many regions with identical temperature"
    assert len(droughts) > 5, "Too many regions with identical drought"
