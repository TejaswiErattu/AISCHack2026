"""Tests for Task 1.1: FastAPI project structure."""
import os

from fastapi.testclient import TestClient

from backend.main import app
from backend.config import Settings


client = TestClient(app)


def test_health_endpoint():
    """GET /health returns {"status": "ok"}."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_cors_headers():
    """CORS headers present in response."""
    resp = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" in resp.headers


def test_config_defaults():
    """Config loads defaults when .env is missing."""
    s = Settings(_env_file="nonexistent.env")
    assert s.DATABASE_URL == "sqlite:///./terralend.db"
    assert s.DEMO_MODE is True
    assert s.NOAA_API_KEY == ""


def test_config_from_env(monkeypatch):
    """Config loads from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("NOAA_API_KEY", "testkey123")
    s = Settings(_env_file="nonexistent.env")
    assert s.DATABASE_URL == "sqlite:///./test.db"
    assert s.DEMO_MODE is False
    assert s.NOAA_API_KEY == "testkey123"
