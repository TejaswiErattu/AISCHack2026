"""Tests for Task 2.3: Climate data orchestrator."""
import logging

import pytest

from backend.services.climate_data import get_climate_data
from backend.seed import REGIONS

REQUIRED_KEYS = {"temperature_anomaly", "drought_index", "rainfall_anomaly", "ndvi_score", "soil_moisture"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _patch_demo_mode(monkeypatch, value: bool):
    """Set DEMO_MODE on the settings singleton."""
    from backend.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", value)


def _patch_noaa(monkeypatch, return_value):
    """Mock fetch_noaa_data to return a fixed value."""
    async def mock_fetch(lat, lng, api_key):
        return return_value
    monkeypatch.setattr("backend.services.climate_data.fetch_noaa_data", mock_fetch)


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_returns_mock_in_demo_mode(monkeypatch):
    """Returns mock data when DEMO_MODE=true."""
    _patch_demo_mode(monkeypatch, True)
    result = await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert result is not None
    assert set(result.keys()) == REQUIRED_KEYS
    # Should match mock values for central valley
    assert result["temperature_anomaly"] == 1.2


@pytest.mark.asyncio
async def test_returns_noaa_when_available(monkeypatch):
    """Returns NOAA data when NOAA succeeds and DEMO_MODE=false."""
    _patch_demo_mode(monkeypatch, False)
    noaa_data = {
        "temperature_anomaly": 3.5,
        "drought_index": 60.0,
        "rainfall_anomaly": -25.0,
        "ndvi_score": None,      # NOAA doesn't provide this
        "soil_moisture": None,   # NOAA doesn't provide this
    }
    _patch_noaa(monkeypatch, noaa_data)

    result = await get_climate_data("central-valley-ca", 36.75, -119.77)
    # Temp/drought/rain from NOAA
    assert result["temperature_anomaly"] == 3.5
    assert result["drought_index"] == 60.0
    assert result["rainfall_anomaly"] == -25.0
    # ndvi/soil filled from mock
    assert result["ndvi_score"] == 62  # central-valley-ca mock value
    assert result["soil_moisture"] == 40  # central-valley-ca mock value


@pytest.mark.asyncio
async def test_falls_back_to_mock_on_noaa_failure(monkeypatch):
    """Falls back to mock when NOAA fails and DEMO_MODE=false."""
    _patch_demo_mode(monkeypatch, False)
    _patch_noaa(monkeypatch, None)  # NOAA failed

    result = await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert result is not None
    # Should be mock values
    assert result["temperature_anomaly"] == 1.2
    assert result["ndvi_score"] == 62


@pytest.mark.asyncio
async def test_always_returns_all_five_keys(monkeypatch):
    """Return dict always has all 5 required keys."""
    # Test with demo mode
    _patch_demo_mode(monkeypatch, True)
    result = await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert set(result.keys()) == REQUIRED_KEYS

    # Test with NOAA fallback
    _patch_demo_mode(monkeypatch, False)
    _patch_noaa(monkeypatch, None)
    result = await get_climate_data("midwest-corn-belt-ia", 42.03, -93.47)
    assert set(result.keys()) == REQUIRED_KEYS


@pytest.mark.asyncio
async def test_logs_data_source_demo(monkeypatch, caplog):
    """Logs indicate mock data source in DEMO_MODE."""
    _patch_demo_mode(monkeypatch, True)
    with caplog.at_level(logging.INFO):
        await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert "mock" in caplog.text.lower() or "DEMO_MODE" in caplog.text


@pytest.mark.asyncio
async def test_logs_data_source_noaa(monkeypatch, caplog):
    """Logs indicate NOAA data source when NOAA succeeds."""
    _patch_demo_mode(monkeypatch, False)
    noaa_data = {
        "temperature_anomaly": 2.0,
        "drought_index": 40.0,
        "rainfall_anomaly": -10.0,
        "ndvi_score": None,
        "soil_moisture": None,
    }
    _patch_noaa(monkeypatch, noaa_data)
    with caplog.at_level(logging.INFO):
        await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert "noaa" in caplog.text.lower()


@pytest.mark.asyncio
async def test_logs_data_source_fallback(monkeypatch, caplog):
    """Logs indicate fallback when NOAA fails."""
    _patch_demo_mode(monkeypatch, False)
    _patch_noaa(monkeypatch, None)
    with caplog.at_level(logging.INFO):
        await get_climate_data("central-valley-ca", 36.75, -119.77)
    assert "fallback" in caplog.text.lower() or "mock" in caplog.text.lower()


@pytest.mark.asyncio
async def test_works_for_all_regions(monkeypatch):
    """Works for all 20+ seeded regions in DEMO_MODE."""
    _patch_demo_mode(monkeypatch, True)
    for region in REGIONS:
        result = await get_climate_data(region["region_id"], region["lat"], region["lng"])
        assert result is not None, f"No data for {region['region_id']}"
        assert set(result.keys()) == REQUIRED_KEYS, f"Missing keys for {region['region_id']}"
