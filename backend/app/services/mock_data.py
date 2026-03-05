from __future__ import annotations

from dataclasses import dataclass, asdict
import random
import time
from typing import Dict, Any


@dataclass
class ClimateSnapshot:
    # Raw-ish values (some are already indices, some are anomalies)
    temperature_anomaly_c: float      # e.g. -2.0 to +5.0
    drought_index: float              # 0 to 100 (higher = worse)
    rainfall_anomaly_pct: float       # e.g. -80 to +80 (negative = drier)
    ndvi_score: float                 # 0 to 100 (higher = healthier)
    soil_moisture: float              # 0 to 100 (higher = wetter/better)
    source: str                       # "mock"
    generated_at_epoch: int           # for debugging/demo


def _stable_seed(region_id: str) -> int:
    """
    Convert region_id into a stable integer seed.
    This ensures the mock climate values don't randomly change every refresh.
    """
    seed = 0
    for ch in region_id:
        seed = (seed * 31 + ord(ch)) % 2_147_483_647
    return seed


def get_mock_climate(region_id: str) -> Dict[str, Any]:
    """
    Returns a dict matching the climate fields we want across the backend.
    """
    rng = random.Random(_stable_seed(region_id))

    # Make values feel realistic-ish for a demo
    temperature_anomaly_c = round(rng.uniform(-1.5, 4.5), 2)
    drought_index = round(rng.uniform(10, 95), 1)
    rainfall_anomaly_pct = round(rng.uniform(-70, 50), 1)

    # NDVI tends to be lower when drought is high (rough correlation)
    ndvi_base = 90 - (drought_index * 0.6) + rng.uniform(-8, 8)
    ndvi_score = round(max(5, min(95, ndvi_base)), 1)

    # Soil moisture also anticorrelates with drought
    soil_base = 85 - (drought_index * 0.7) + rng.uniform(-10, 10)
    soil_moisture = round(max(5, min(95, soil_base)), 1)

    snap = ClimateSnapshot(
        temperature_anomaly_c=temperature_anomaly_c,
        drought_index=drought_index,
        rainfall_anomaly_pct=rainfall_anomaly_pct,
        ndvi_score=ndvi_score,
        soil_moisture=soil_moisture,
        source="mock",
        generated_at_epoch=int(time.time()),
    )
    return asdict(snap)
