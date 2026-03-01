"""Tests for Task 2.1: Mock climate data layer."""
from backend.services.mock_data import get_mock_climate
from backend.seed import REGIONS


def test_returns_data_for_all_regions():
    """get_mock_climate() returns data for all 20 seeded regions."""
    for region in REGIONS:
        result = get_mock_climate(region["region_id"])
        assert result is not None, f"No data for {region['region_id']}"


def test_returns_none_for_unknown_region():
    """Returns None for unknown region_id."""
    assert get_mock_climate("nonexistent-region") is None
    assert get_mock_climate("") is None


def test_values_within_valid_ranges():
    """All values within valid ranges per spec."""
    for region in REGIONS:
        data = get_mock_climate(region["region_id"])
        rid = region["region_id"]
        assert -5 <= data["temperature_anomaly"] <= 8, f"{rid} temp out of range"
        assert 0 <= data["drought_index"] <= 100, f"{rid} drought out of range"
        assert -80 <= data["rainfall_anomaly"] <= 80, f"{rid} rain out of range"
        assert 0 <= data["ndvi_score"] <= 100, f"{rid} ndvi out of range"
        assert 0 <= data["soil_moisture"] <= 100, f"{rid} soil out of range"


def test_different_regions_return_different_values():
    """Different regions return different values (not all identical)."""
    all_data = [get_mock_climate(r["region_id"]) for r in REGIONS]
    temps = {d["temperature_anomaly"] for d in all_data}
    droughts = {d["drought_index"] for d in all_data}
    assert len(temps) > 5, "Too many regions with identical temperature"
    assert len(droughts) > 5, "Too many regions with identical drought"


def test_returns_all_five_keys():
    """Return dict has all 5 required climate fields."""
    expected_keys = {"temperature_anomaly", "drought_index", "rainfall_anomaly", "ndvi_score", "soil_moisture"}
    data = get_mock_climate("central-valley-ca")
    assert set(data.keys()) == expected_keys


def test_returns_copy_not_reference():
    """Returned dict is a copy, not a reference to the source data."""
    d1 = get_mock_climate("central-valley-ca")
    d1["temperature_anomaly"] = 999
    d2 = get_mock_climate("central-valley-ca")
    assert d2["temperature_anomaly"] != 999
