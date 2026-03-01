from sqlalchemy import Column, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func

from backend.models.database import Base


class Region(Base):
    __tablename__ = "regions"

    region_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    primary_crop = Column(String, nullable=False)
    base_loan_rate = Column(Float, nullable=False)
    base_pd = Column(Float, nullable=False)
    base_premium = Column(Float, nullable=False)


class ClimateSnapshot(Base):
    __tablename__ = "climate_snapshots"

    snapshot_id = Column(String, primary_key=True)
    region_id = Column(String, ForeignKey("regions.region_id"), nullable=False)
    temperature_anomaly = Column(Float, nullable=False)
    drought_index = Column(Float, nullable=False)
    rainfall_anomaly = Column(Float, nullable=False)
    ndvi_score = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    yield_stress_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class FinancialOutput(Base):
    __tablename__ = "financial_outputs"

    output_id = Column(String, primary_key=True)
    region_id = Column(String, ForeignKey("regions.region_id"), nullable=False)
    snapshot_id = Column(String, ForeignKey("climate_snapshots.snapshot_id"), nullable=False)
    interest_rate = Column(Float, nullable=False)
    probability_of_default = Column(Float, nullable=False)
    insurance_premium = Column(Float, nullable=False)
    repayment_flexibility = Column(Float, nullable=False)
    baseline_rate = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    run_id = Column(String, primary_key=True)
    region_id = Column(String, ForeignKey("regions.region_id"), nullable=False)
    input_overrides = Column(JSON, nullable=True)
    stress_score = Column(Float, nullable=False)
    financial_outputs = Column(JSON, nullable=True)
    narrative = Column(String, nullable=True)
    panel_context = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
