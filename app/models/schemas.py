from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class LiteracyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TransferStatus(str, Enum):
    PENDING = "pending"
    QUOTED = "quoted"
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OnboardingStep(str, Enum):
    LANGUAGE = "language"
    LITERACY = "literacy"
    SENDER_COUNTRY = "sender_country"
    RECIPIENT_COUNTRY = "recipient_country"
    AMOUNT = "amount"
    CONFIRM = "confirm"
    COMPLETE = "complete"


class User(BaseModel):
    user_id: str
    telegram_chat_id: str
    language: str = "en"
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    onboarding_step: OnboardingStep = OnboardingStep.LANGUAGE


class RemittanceProfile(BaseModel):
    profile_id: str
    user_id: str
    sender_country: str = ""
    recipient_country: str = ""
    corridor: str = ""  # e.g. "USD_INR"
    average_amount: float = 0.0
    payout_method: str = "bank_transfer"
    execution_enabled: bool = False  # Only True for US→India


class UserPreferences(BaseModel):
    user_id: str
    financial_literacy_level: LiteracyLevel = LiteracyLevel.BEGINNER
    alert_threshold_pct: float = 1.0  # Default 1% improvement triggers alert
    defaults_applied: bool = True


class RateSnapshot(BaseModel):
    snapshot_id: str
    corridor: str
    provider: str
    rate: float
    fees: float = 0.0
    recipient_amount: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Transfer(BaseModel):
    transfer_id: str
    user_id: str
    provider: str
    amount_sent: float
    currency_from: str
    currency_to: str
    fx_rate: float
    fees: float = 0.0
    recipient_amount: float = 0.0
    status: TransferStatus = TransferStatus.PENDING
    provider_tx_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SavingsRecord(BaseModel):
    user_id: str
    transfer_id: str
    baseline_rate: float
    optimized_rate: float
    personal_savings: float  # Amount saved vs personal baseline
    global_savings: float  # Amount saved vs global baseline
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AlertState(BaseModel):
    """Tracks alert cadence per user/corridor."""
    user_id: str
    corridor: str
    in_favorable_window: bool = False
    full_alert_sent: bool = False
    last_alert_at: datetime | None = None
    user_interacted_since_alert: bool = False
