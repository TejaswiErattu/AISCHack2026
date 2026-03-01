"""Tests for Task 5.3: Simulation endpoint."""


# ── 1. No overrides → same as baseline ───────────────────────────────────────

def test_simulate_no_overrides(seeded_client):
    """Simulate with no overrides returns same as baseline."""
    resp = seeded_client.post("/simulate", json={"region_id": "central-valley-ca"})
    assert resp.status_code == 200
    data = resp.json()
    # With no overrides, simulated should equal baseline
    assert data["stress_score"] == data["baseline_stress"]
    assert data["simulated"]["interest_rate"] == data["baseline"]["interest_rate"]
    assert data["deltas"]["stress_score"] == 0
    assert data["deltas"]["interest_rate"] == 0


# ── 2. Temperature delta +5 → higher stress/rate ────────────────────────────

def test_simulate_temp_increase(seeded_client):
    """Simulate with temperature_delta +5 returns higher stress and rate."""
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "temperature_delta": 5.0,
    })
    data = resp.json()
    assert data["stress_score"] > data["baseline_stress"]
    assert data["simulated"]["interest_rate"] > data["baseline"]["interest_rate"]
    assert data["deltas"]["stress_score"] > 0
    assert data["deltas"]["interest_rate"] > 0


# ── 3. Drought index 100 → near-max stress ──────────────────────────────────

def test_simulate_max_drought(seeded_client):
    """Simulate with drought_index 100 returns high stress."""
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "drought_index": 100,
    })
    data = resp.json()
    assert data["stress_score"] > data["baseline_stress"]
    # With drought at 100, stress should be significantly elevated
    assert data["stress_score"] > 40


# ── 4. Response includes deltas ──────────────────────────────────────────────

def test_simulate_deltas_present(seeded_client):
    """Response includes deltas for stress and all financial fields."""
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "temperature_delta": 2.0,
    })
    data = resp.json()
    deltas = data["deltas"]
    assert "stress_score" in deltas
    assert "interest_rate" in deltas
    assert "probability_of_default" in deltas
    assert "insurance_premium" in deltas
    assert "repayment_flexibility" in deltas


# ── 5. 404 for invalid region_id ─────────────────────────────────────────────

def test_simulate_404(seeded_client):
    """404 for invalid region_id."""
    resp = seeded_client.post("/simulate", json={"region_id": "nonexistent"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Region not found"


# ── 6. Partial overrides work ────────────────────────────────────────────────

def test_simulate_partial_overrides(seeded_client):
    """Partial overrides work — only temperature_delta, others use current values."""
    # Get baseline first
    resp_base = seeded_client.post("/simulate", json={"region_id": "central-valley-ca"})
    baseline_stress = resp_base.json()["baseline_stress"]

    # Override only temperature
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "temperature_delta": 3.0,
    })
    data = resp.json()
    # Stress should change (because temp changed)
    assert data["stress_score"] != baseline_stress
    # But baseline_stress should be the same (unchanged current climate)
    assert data["baseline_stress"] == baseline_stress


# ── 7. Extreme overrides don't crash ─────────────────────────────────────────

def test_simulate_extreme_overrides(seeded_client):
    """Extreme overrides don't crash — values are clamped gracefully."""
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "temperature_delta": 100,
        "drought_index": 999,
        "rainfall_anomaly": -500,
    })
    assert resp.status_code == 200
    data = resp.json()
    # Stress should be clamped to 0–100
    assert 0 <= data["stress_score"] <= 100
    # Financial values should be within clamped ranges
    assert 3.0 <= data["simulated"]["interest_rate"] <= 15.0
    assert 0.01 <= data["simulated"]["probability_of_default"] <= 0.50


# ── 8. Response includes both new values and baseline values ─────────────────

def test_simulate_has_both_values(seeded_client):
    """Response includes both simulated and baseline financial values."""
    resp = seeded_client.post("/simulate", json={
        "region_id": "central-valley-ca",
        "temperature_delta": 2.0,
    })
    data = resp.json()
    # Both baseline and simulated should be full FinancialResponse objects
    for key in ["interest_rate", "probability_of_default", "insurance_premium", "repayment_flexibility", "baseline_rate"]:
        assert key in data["baseline"], f"baseline missing {key}"
        assert key in data["simulated"], f"simulated missing {key}"
    # stress scores present
    assert "stress_score" in data
    assert "baseline_stress" in data
    assert "region_id" in data
