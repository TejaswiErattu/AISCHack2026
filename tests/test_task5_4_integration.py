"""Tests for Task 5.4: Full integration — wiring, startup, end-to-end flow."""


# ── 1. Full integration: start → seed → all endpoints work ──────────────────

def test_full_integration_flow(seeded_client):
    """Full end-to-end: regions → climate → stress → financial → simulate."""
    # Step 1: GET /regions returns seeded data
    resp = seeded_client.get("/regions")
    assert resp.status_code == 200
    regions = resp.json()
    assert len(regions) >= 20
    region_id = regions[0]["region_id"]

    # Step 2: GET /region/{id}/climate works
    resp = seeded_client.get(f"/region/{region_id}/climate")
    assert resp.status_code == 200
    climate = resp.json()
    assert "temperature_anomaly" in climate

    # Step 3: GET /region/{id}/stress works
    resp = seeded_client.get(f"/region/{region_id}/stress")
    assert resp.status_code == 200
    stress = resp.json()
    assert 0 <= stress["yield_stress_score"] <= 100

    # Step 4: GET /region/{id}/financial works
    resp = seeded_client.get(f"/region/{region_id}/financial")
    assert resp.status_code == 200
    financial = resp.json()
    assert "interest_rate" in financial

    # Step 5: GET /region/{id}/comparison works
    resp = seeded_client.get(f"/region/{region_id}/comparison")
    assert resp.status_code == 200
    comparison = resp.json()
    assert "old_system" in comparison
    assert "terralend" in comparison

    # Step 6: POST /simulate works
    resp = seeded_client.post("/simulate", json={
        "region_id": region_id,
        "temperature_delta": 2.0,
    })
    assert resp.status_code == 200
    sim = resp.json()
    assert sim["stress_score"] > sim["baseline_stress"]

    # Step 7: Health check still works
    resp = seeded_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── 2. CORS preflight requests pass ──────────────────────────────────────────

def test_cors_preflight(seeded_client):
    """CORS preflight (OPTIONS) requests return correct headers."""
    resp = seeded_client.options(
        "/regions",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert "access-control-allow-origin" in resp.headers
    assert "access-control-allow-methods" in resp.headers


def test_cors_on_post(seeded_client):
    """CORS headers present on POST responses too."""
    resp = seeded_client.post(
        "/simulate",
        json={"region_id": "central-valley-ca"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert "access-control-allow-origin" in resp.headers


# ── 3. Starts clean from empty DB (tables + seed) ────────────────────────────

def test_starts_clean_empty_db(seeded_client):
    """App starts and serves data from a freshly created + seeded DB."""
    # The seeded_client fixture creates an empty in-memory DB, creates tables,
    # seeds it, then runs. If we get here with data, startup works.
    resp = seeded_client.get("/regions")
    assert resp.status_code == 200
    assert len(resp.json()) >= 20


# ── 4. Starts clean with existing DB (idempotent seed) ───────────────────────

def test_idempotent_startup(seeded_client):
    """Calling seed again doesn't duplicate data (tested via consistent count)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from backend.models.database import Base
    from backend.models.models import Region
    from backend.seed import seed_database

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # Seed twice
    db = Session()
    seed_database(db)
    count1 = db.query(Region).count()
    seed_database(db)
    count2 = db.query(Region).count()
    db.close()

    assert count1 == count2


# ── 5. All endpoints return proper JSON content-type ─────────────────────────

def test_json_content_type(seeded_client):
    """All endpoints return application/json content-type."""
    endpoints = [
        ("GET", "/health"),
        ("GET", "/regions"),
        ("GET", "/region/central-valley-ca/climate"),
        ("GET", "/region/central-valley-ca/stress"),
        ("GET", "/region/central-valley-ca/financial"),
        ("GET", "/region/central-valley-ca/comparison"),
    ]
    for method, path in endpoints:
        resp = seeded_client.request(method, path)
        assert "application/json" in resp.headers.get("content-type", ""), \
            f"{method} {path} missing JSON content-type"

    # POST simulate
    resp = seeded_client.post("/simulate", json={"region_id": "central-valley-ca"})
    assert "application/json" in resp.headers.get("content-type", "")


# ── 6. Error responses follow consistent format ─────────────────────────────

def test_error_format_consistency(seeded_client):
    """Error responses follow {"detail": "..."} format."""
    # 404 on all region-specific endpoints
    for path in [
        "/region/nonexistent/climate",
        "/region/nonexistent/stress",
        "/region/nonexistent/financial",
        "/region/nonexistent/comparison",
    ]:
        resp = seeded_client.get(path)
        assert resp.status_code == 404
        body = resp.json()
        assert "detail" in body
        assert isinstance(body["detail"], str)

    # 404 on simulate
    resp = seeded_client.post("/simulate", json={"region_id": "nonexistent"})
    assert resp.status_code == 404
    assert "detail" in resp.json()
