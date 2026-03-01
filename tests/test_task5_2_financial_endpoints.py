"""Tests for Task 5.2: Financial endpoints."""


# ── 1. Financial endpoint returns all fields ─────────────────────────────────

def test_financial_all_fields(seeded_client):
    """Financial endpoint returns all required fields."""
    resp = seeded_client.get("/region/central-valley-ca/financial")
    assert resp.status_code == 200
    data = resp.json()
    assert "interest_rate" in data
    assert "probability_of_default" in data
    assert "insurance_premium" in data
    assert "repayment_flexibility" in data
    assert "baseline_rate" in data


# ── 2. Comparison endpoint returns old_system and terralend ──────────────────

def test_comparison_structure(seeded_client):
    """Comparison endpoint returns old_system and terralend objects."""
    resp = seeded_client.get("/region/central-valley-ca/comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert "old_system" in data
    assert "terralend" in data
    # Both should have the same set of financial fields
    for key in ["interest_rate", "probability_of_default", "insurance_premium", "repayment_flexibility"]:
        assert key in data["old_system"], f"old_system missing {key}"
        assert key in data["terralend"], f"terralend missing {key}"


# ── 3. Old system values are static ──────────────────────────────────────────

def test_old_system_static(seeded_client):
    """Old system values don't change between calls (they're seeded, static)."""
    resp1 = seeded_client.get("/region/central-valley-ca/comparison")
    resp2 = seeded_client.get("/region/central-valley-ca/comparison")
    old1 = resp1.json()["old_system"]
    old2 = resp2.json()["old_system"]
    assert old1 == old2


# ── 4. TerraLend values reflect climate data ─────────────────────────────────

def test_terralend_reflects_climate(seeded_client):
    """TerraLend values are dynamically computed, not identical to old system."""
    resp = seeded_client.get("/region/central-valley-ca/comparison")
    data = resp.json()
    # TerraLend rate should differ from old system (climate-adjusted vs static)
    # They use different formulas, so values should not be identical
    assert data["terralend"]["interest_rate"] != data["old_system"]["interest_rate"] or \
           data["terralend"]["probability_of_default"] != data["old_system"]["probability_of_default"]


# ── 5. 404 for invalid region_id on both endpoints ──────────────────────────

def test_financial_404(seeded_client):
    """404 for invalid region_id on financial endpoint."""
    resp = seeded_client.get("/region/nonexistent/financial")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Region not found"


def test_comparison_404(seeded_client):
    """404 for invalid region_id on comparison endpoint."""
    resp = seeded_client.get("/region/nonexistent/comparison")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Region not found"


# ── 6. Financial values within clamped ranges ────────────────────────────────

def test_financial_values_clamped(seeded_client):
    """Financial values are within spec-defined clamped ranges."""
    # Test across multiple regions
    for region_id in ["central-valley-ca", "texas-panhandle-tx", "willamette-valley-or"]:
        resp = seeded_client.get(f"/region/{region_id}/financial")
        data = resp.json()
        assert 3.0 <= data["interest_rate"] <= 15.0, \
            f"{region_id} rate {data['interest_rate']} out of range"
        assert 0.01 <= data["probability_of_default"] <= 0.50, \
            f"{region_id} PD {data['probability_of_default']} out of range"
        assert data["insurance_premium"] > 0, \
            f"{region_id} premium should be positive"
        assert 0 <= data["repayment_flexibility"] <= 100, \
            f"{region_id} flexibility {data['repayment_flexibility']} out of range"
