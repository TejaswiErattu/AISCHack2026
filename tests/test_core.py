"""Core tests for RemitAgent — verifies basic functionality."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    LiteracyLevel,
    OnboardingStep,
    TransferStatus,
    User,
)
from app.services.decision_engine import (
    compute_recipient_amount,
    compute_savings,
    evaluate_threshold,
)


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_user_model():
    user = User(user_id="test-123", telegram_chat_id="456")
    assert user.language == "en"
    assert user.onboarding_step == OnboardingStep.LANGUAGE


def test_compute_recipient_amount():
    # $500 sent, $5 fee, rate 83.5
    result = compute_recipient_amount(500.0, 5.0, 83.5)
    assert result == pytest.approx(41332.5)


def test_compute_savings():
    savings = compute_savings(41500.0, 41000.0)
    assert savings["absolute"] == pytest.approx(500.0)
    assert savings["percentage"] == pytest.approx(1.2195, rel=1e-3)


def test_evaluate_threshold_met():
    assert evaluate_threshold(41500.0, 41000.0, 1.0) is True


def test_evaluate_threshold_not_met():
    assert evaluate_threshold(41050.0, 41000.0, 1.0) is False


def test_fallback_templates():
    from app.llm.fallbacks import FallbackTemplates

    alert = FallbackTemplates.rate_alert(83420, 82040, 1.68, "INR")
    assert "83,420" in alert or "83420" in alert
    assert "INR" in alert

    short = FallbackTemplates.short_followup(83420, 1.68, "INR")
    assert "INR" in short

    question = FallbackTemplates.onboarding_question("language")
    assert len(question) > 0


def test_stablecoin_route_estimation():
    """Test that stablecoin fee math is correct."""
    # Simulate: $500 → USDC (0.1% fee) → INR (0.5% off-ramp fee)
    amount = 500.0
    on_ramp_fee = 0.001
    off_ramp_fee = 0.005
    usdc_rate = 83.5  # USDC to INR

    after_on_ramp = amount * (1 - on_ramp_fee)
    usdc_amount = after_on_ramp  # 1:1 USD to USDC
    after_off_ramp = usdc_amount * usdc_rate * (1 - off_ramp_fee)

    assert after_on_ramp == pytest.approx(499.5)
    assert after_off_ramp == pytest.approx(499.5 * 83.5 * 0.995, rel=1e-3)
