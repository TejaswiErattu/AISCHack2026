"""Deterministic replay mode — replay stored rate data when APIs are down.

Usage: python -m scripts.demo_replay
"""

import asyncio
import logging

from app.db import crud

logger = logging.getLogger(__name__)

# Pre-defined demo rate sequence for USD_INR (simulates a favorable window)
DEMO_RATES = [
    {"rate": 82.80, "label": "baseline"},
    {"rate": 82.95, "label": "slight improvement"},
    {"rate": 83.20, "label": "approaching threshold"},
    {"rate": 83.65, "label": "FAVORABLE — alert triggered"},
    {"rate": 83.80, "label": "still favorable — short follow-up"},
    {"rate": 83.50, "label": "slight pullback"},
    {"rate": 83.70, "label": "recovery"},
    {"rate": 82.90, "label": "back to baseline"},
]


async def run_demo_replay(corridor: str = "USD_INR", amount: float = 500.0):
    """Replay a deterministic rate sequence, storing snapshots and triggering alerts."""
    from app.services.rate_monitor import store_snapshot

    print(f"\n{'='*60}")
    print(f"  DEMO REPLAY MODE — {corridor}")
    print(f"  Amount: ${amount}")
    print(f"{'='*60}\n")

    for i, entry in enumerate(DEMO_RATES):
        rate = entry["rate"]
        label = entry["label"]
        recipient_amount = amount * rate

        print(f"  Step {i+1}/{len(DEMO_RATES)}: rate={rate:.2f} → "
              f"recipient={recipient_amount:,.2f} — {label}")

        await store_snapshot(
            corridor=corridor,
            rate=rate,
            fees=0.0,
            amount_sent=amount,
            provider="demo_replay",
        )

        # Check baseline after enough data
        if i >= 3:
            from app.services.rate_monitor import compute_personal_baseline

            baseline = await compute_personal_baseline(corridor)
            if baseline:
                diff = recipient_amount - baseline["avg_recipient_amount"]
                pct = (diff / baseline["avg_recipient_amount"]) * 100
                print(f"           baseline avg: {baseline['avg_recipient_amount']:,.2f} "
                      f"(diff: {diff:+,.2f}, {pct:+.2f}%)")

    print(f"\n{'='*60}")
    print("  Demo replay complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run_demo_replay())
