"""Mock Wise provider — deterministic transfer IDs for demo fallback.

Used when Wise sandbox is unavailable. Returns realistic-looking responses
with predictable IDs for demo scripting.
"""

import uuid
from datetime import UTC, datetime


_MOCK_COUNTER = 0


def _next_id() -> str:
    global _MOCK_COUNTER
    _MOCK_COUNTER += 1
    return f"MOCK-{_MOCK_COUNTER:04d}"


async def create_quote(
    source_currency: str, target_currency: str, amount: float
) -> dict:
    """Return a mock quote with a deterministic structure."""
    # Use a realistic demo rate for USD→INR
    rates = {
        ("USD", "INR"): 83.50,
        ("GBP", "INR"): 104.20,
        ("USD", "PHP"): 55.80,
    }
    rate = rates.get((source_currency, target_currency), 83.50)
    fee = round(amount * 0.01, 2)  # 1% fee

    return {
        "id": _next_id(),
        "source": source_currency,
        "target": target_currency,
        "sourceAmount": amount,
        "targetAmount": round((amount - fee) * rate, 2),
        "rate": rate,
        "fee": fee,
        "type": "REGULAR",
        "createdTime": datetime.now(UTC).isoformat(),
        "mock": True,
    }


async def create_transfer(quote_id: str, target_account: str = "") -> dict:
    """Return a mock transfer result."""
    return {
        "id": _next_id(),
        "quoteId": quote_id,
        "targetAccount": target_account or "demo-recipient",
        "status": "processing",
        "reference": f"REMIT-{uuid.uuid4().hex[:8].upper()}",
        "createdTime": datetime.now(UTC).isoformat(),
        "mock": True,
    }


async def get_transfer_status(transfer_id: str) -> dict:
    """Return a mock transfer status — always shows completed for demo."""
    return {
        "id": transfer_id,
        "status": "funds_converted",
        "sourceCurrency": "USD",
        "targetCurrency": "INR",
        "createdTime": datetime.now(UTC).isoformat(),
        "mock": True,
    }
