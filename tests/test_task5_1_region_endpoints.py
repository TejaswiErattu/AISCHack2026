"""Tests for Task 5.1: Region endpoints."""


# ── 1. GET /regions returns 20+ regions ──────────────────────────────────────

def test_list_regions_count(seeded_client):
    """GET /regions returns 20+ regions."""
    resp = seeded_client.get("/regions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 20


# ── 2. GET /regions response matches RegionResponse schema ──────────────────

def test_list_regions_schema(seeded_client):
    """GET /regions response matches List[RegionResponse] schema."""
    resp = seeded_client.get("/regions")
    data = resp.json()
    for region in data:
        assert "region_id" in region
        assert "name" in region
        assert "lat" in region
        assert "lng" in region
        assert "primary_crop" in region
        # Should NOT expose base financial fields (those aren't in RegionResponse)
        assert "base_loan_rate" not in region


# ── 3. GET /region/{id}/climate returns valid climate data ───────────────────

def test_get_climate_valid_region(seeded_client):
    """GET /region/central-valley-ca/climate returns valid climate data."""
    resp = seeded_client.get("/region/central-valley-ca/climate")
    assert resp.status_code == 200
    data = resp.json()
    assert "temperature_anomaly" in data
    assert "drought_index" in data
    assert "rainfall_anomaly" in data
    assert "ndvi_score" in data
    assert "soil_moisture" in data
    # Values should be within valid ranges
    assert 0 <= data["drought_index"] <= 100
    assert 0 <= data["ndvi_score"] <= 100
    assert 0 <= data["soil_moisture"] <= 100


# ── 4. GET /region/nonexistent/climate returns 404 ───────────────────────────

def test_get_climate_404(seeded_client):
    """GET /region/nonexistent/climate returns 404."""
    resp = seeded_client.get("/region/nonexistent/climate")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Region not found"


# ── 5. GET /region/{id}/stress returns float 0–100 ──────────────────────────

def test_get_stress_valid_region(seeded_client):
    """GET /region/central-valley-ca/stress returns float 0–100."""
    resp = seeded_client.get("/region/central-valley-ca/stress")
    assert resp.status_code == 200
    data = resp.json()
    assert "yield_stress_score" in data
    assert 0 <= data["yield_stress_score"] <= 100


# ── 6. Stress endpoint returns breakdown ─────────────────────────────────────

def test_get_stress_breakdown(seeded_client):
    """Stress endpoint returns breakdown showing which factors contribute most."""
    resp = seeded_client.get("/region/central-valley-ca/stress")
    data = resp.json()
    assert "breakdown" in data
    breakdown = data["breakdown"]
    assert "heat_stress" in breakdown
    assert "drought" in breakdown
    assert "rainfall_anomaly" in breakdown
    assert "ndvi_deficit" in breakdown
    assert "soil_moisture_deficit" in breakdown
    # Each contribution should be a non-negative number
    for key, val in breakdown.items():
        assert val >= 0, f"Breakdown {key} should be non-negative, got {val}"


# ── Additional: 404 on stress endpoint too ───────────────────────────────────

def test_get_stress_404(seeded_client):
    """GET /region/nonexistent/stress returns 404."""
    resp = seeded_client.get("/region/nonexistent/stress")
    assert resp.status_code == 404
