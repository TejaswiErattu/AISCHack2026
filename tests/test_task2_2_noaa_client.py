"""Tests for Task 2.2: NOAA API integration.

All tests use mocked HTTP responses — no real NOAA API calls.
"""
import pytest
import httpx

from backend.services.noaa_client import fetch_noaa_data, _normalize_noaa_response


# ── Helper: build a fake NOAA response ──────────────────────────────────────

def _make_noaa_response(temps=None, precip=None):
    """Build a realistic NOAA CDO API response dict."""
    results = []
    for t in (temps or []):
        results.append({"datatype": "TMAX", "value": t, "date": "2025-01-01", "station": "GHCND:USW00023174"})
    for p in (precip or []):
        results.append({"datatype": "PRCP", "value": p, "date": "2025-01-01", "station": "GHCND:USW00023174"})
    return {"results": results}


# ── Tests: successful normalized response ────────────────────────────────────

@pytest.mark.asyncio
async def test_returns_normalized_dict_on_success(monkeypatch):
    """Function returns normalized dict with expected keys when mocked NOAA response given."""
    noaa_json = _make_noaa_response(temps=[22.0, 24.0], precip=[60.0, 30.0])

    async def mock_get(self, url, **kwargs):
        return httpx.Response(200, json=noaa_json, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_noaa_data(36.75, -119.77, "test-api-key")

    assert result is not None
    assert "temperature_anomaly" in result
    assert "drought_index" in result
    assert "rainfall_anomaly" in result
    assert "ndvi_score" in result  # None but present
    assert "soil_moisture" in result  # None but present
    assert isinstance(result["temperature_anomaly"], float)


# ── Tests: graceful error handling ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_handles_timeout_gracefully(monkeypatch):
    """Handles NOAA API timeout gracefully (returns None, does not crash)."""
    async def mock_get(self, url, **kwargs):
        raise httpx.TimeoutException("Connection timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_noaa_data(36.75, -119.77, "test-api-key")
    assert result is None


@pytest.mark.asyncio
async def test_handles_429_rate_limit(monkeypatch):
    """Handles NOAA 429 rate limit response gracefully."""
    async def mock_get(self, url, **kwargs):
        return httpx.Response(429, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_noaa_data(36.75, -119.77, "test-api-key")
    assert result is None


@pytest.mark.asyncio
async def test_handles_malformed_response(monkeypatch):
    """Handles malformed NOAA response (missing fields) gracefully."""
    async def mock_get(self, url, **kwargs):
        # Response with no 'results' key
        return httpx.Response(200, json={"metadata": {}}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_noaa_data(36.75, -119.77, "test-api-key")
    assert result is None


@pytest.mark.asyncio
async def test_handles_network_error(monkeypatch):
    """Handles network error gracefully."""
    async def mock_get(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_noaa_data(36.75, -119.77, "test-api-key")
    assert result is None


@pytest.mark.asyncio
async def test_handles_empty_api_key():
    """Returns None when no API key is provided."""
    result = await fetch_noaa_data(36.75, -119.77, "")
    assert result is None


# ── Tests: normalization logic ───────────────────────────────────────────────

def test_normalize_empty_results():
    """Normalization returns None for empty results list."""
    assert _normalize_noaa_response({"results": []}) is None


def test_normalize_no_temps():
    """Normalization returns None when only precip data, no temperature."""
    data = _make_noaa_response(temps=[], precip=[50.0])
    assert _normalize_noaa_response(data) is None


def test_normalize_temp_anomaly_clamped():
    """Temperature anomaly is clamped to -5..+8 range."""
    # Very hot: avg 30°C, baseline 20°C → anomaly +10 → clamped to +8
    data = _make_noaa_response(temps=[30.0], precip=[80.0])
    result = _normalize_noaa_response(data)
    assert result["temperature_anomaly"] == 8.0

    # Very cold: avg 10°C, baseline 20°C → anomaly -10 → clamped to -5
    data = _make_noaa_response(temps=[10.0], precip=[80.0])
    result = _normalize_noaa_response(data)
    assert result["temperature_anomaly"] == -5.0
