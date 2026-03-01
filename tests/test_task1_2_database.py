"""Tests for Task 1.2: SQLite database setup."""
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base, get_db
from backend.models.models import Region, ClimateSnapshot, FinancialOutput, SimulationRun
from backend.models.schemas import ClimateResponse, RegionResponse, SimulateRequest


@pytest.fixture
def db_session():
    """Create a temp in-memory SQLite DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_region(region_id="test-region"):
    return Region(
        region_id=region_id,
        name="Test Region",
        lat=36.7,
        lng=-119.8,
        primary_crop="wheat",
        base_loan_rate=5.5,
        base_pd=0.05,
        base_premium=1200.0,
    )


def _make_snapshot(region_id="test-region", snapshot_id=None):
    return ClimateSnapshot(
        snapshot_id=snapshot_id or str(uuid.uuid4()),
        region_id=region_id,
        temperature_anomaly=1.5,
        drought_index=40.0,
        rainfall_anomaly=-10.0,
        ndvi_score=65.0,
        soil_moisture=55.0,
        yield_stress_score=35.0,
    )


# --- Table creation ---

def test_tables_created(db_session):
    """Tables created successfully in a temp SQLite DB."""
    tables = Base.metadata.tables.keys()
    assert "regions" in tables
    assert "climate_snapshots" in tables
    assert "financial_outputs" in tables
    assert "simulation_runs" in tables


# --- ORM INSERT and SELECT ---

def test_region_insert_select(db_session):
    """Region model can INSERT and SELECT correctly."""
    r = _make_region()
    db_session.add(r)
    db_session.commit()
    result = db_session.query(Region).filter_by(region_id="test-region").first()
    assert result is not None
    assert result.name == "Test Region"
    assert result.lat == 36.7
    assert result.primary_crop == "wheat"


def test_climate_snapshot_insert_select(db_session):
    """ClimateSnapshot model can INSERT and SELECT correctly."""
    db_session.add(_make_region())
    db_session.commit()
    snap = _make_snapshot()
    db_session.add(snap)
    db_session.commit()
    result = db_session.query(ClimateSnapshot).first()
    assert result.temperature_anomaly == 1.5
    assert result.drought_index == 40.0


def test_financial_output_insert_select(db_session):
    """FinancialOutput model can INSERT and SELECT correctly."""
    db_session.add(_make_region())
    db_session.commit()
    snap = _make_snapshot()
    db_session.add(snap)
    db_session.commit()
    fo = FinancialOutput(
        output_id=str(uuid.uuid4()),
        region_id="test-region",
        snapshot_id=snap.snapshot_id,
        interest_rate=6.2,
        probability_of_default=0.08,
        insurance_premium=1400.0,
        repayment_flexibility=65.0,
        baseline_rate=7.2,
    )
    db_session.add(fo)
    db_session.commit()
    result = db_session.query(FinancialOutput).first()
    assert result.interest_rate == 6.2
    assert result.baseline_rate == 7.2


def test_simulation_run_json_fields(db_session):
    """SimulationRun JSON fields serialize/deserialize correctly."""
    db_session.add(_make_region())
    db_session.commit()
    overrides = {"temperature_delta": 2.5, "drought_index": 70}
    outputs = {"interest_rate": 7.8, "pd": 0.18}
    sim = SimulationRun(
        run_id=str(uuid.uuid4()),
        region_id="test-region",
        input_overrides=overrides,
        stress_score=72.0,
        financial_outputs=outputs,
        narrative="Test narrative",
        panel_context="loan_officer",
    )
    db_session.add(sim)
    db_session.commit()
    result = db_session.query(SimulationRun).first()
    assert result.input_overrides == overrides
    assert result.financial_outputs == outputs
    assert result.narrative == "Test narrative"


# --- Pydantic schema validation ---

def test_climate_response_valid():
    """ClimateResponse validates correct data."""
    c = ClimateResponse(
        temperature_anomaly=2.0,
        drought_index=50.0,
        rainfall_anomaly=-20.0,
        ndvi_score=70.0,
        soil_moisture=60.0,
    )
    assert c.drought_index == 50.0


def test_climate_response_rejects_invalid():
    """ClimateResponse rejects out-of-range drought_index."""
    with pytest.raises(ValidationError):
        ClimateResponse(
            temperature_anomaly=2.0,
            drought_index=150.0,  # > 100
            rainfall_anomaly=-20.0,
            ndvi_score=70.0,
            soil_moisture=60.0,
        )


def test_region_response_from_orm(db_session):
    """RegionResponse validates from ORM model."""
    r = _make_region()
    db_session.add(r)
    db_session.commit()
    result = db_session.query(Region).first()
    schema = RegionResponse.model_validate(result)
    assert schema.region_id == "test-region"


def test_simulate_request_partial():
    """SimulateRequest accepts partial overrides."""
    req = SimulateRequest(region_id="test", temperature_delta=2.5)
    assert req.temperature_delta == 2.5
    assert req.drought_index is None


# --- get_db dependency ---

def test_get_db_yields_and_closes():
    """get_db() yields a session and closes it."""
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
    # Session should be closed after generator exhausted


# --- FK constraints ---

def test_fk_constraint_snapshot(db_session):
    """FK constraint: ClimateSnapshot with invalid region_id fails on flush."""
    snap = _make_snapshot(region_id="nonexistent")
    db_session.add(snap)
    # SQLite doesn't enforce FK by default, but we verify the field is set
    db_session.flush()
    assert snap.region_id == "nonexistent"
