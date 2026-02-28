"""Seed FX rate data — pre-populate 14 days of snapshots for demo baseline.

Usage: python -m scripts.seed_data
"""

import random
import uuid
from datetime import UTC, datetime, timedelta

from app.db.dynamodb import get_table


# Base rates for seeding (mid-market approximations)
SEED_CORRIDORS = {
    "USD_INR": {"base_rate": 83.0, "volatility": 0.5, "amount": 500.0},
    "USD_PHP": {"base_rate": 55.5, "volatility": 0.3, "amount": 300.0},
    "GBP_INR": {"base_rate": 104.0, "volatility": 0.6, "amount": 400.0},
}

SNAPSHOTS_PER_DAY = 96  # every 15 minutes = 96 per day
DAYS_TO_SEED = 14


def seed_rate_snapshots():
    """Generate and store 14 days of rate snapshots for demo corridors."""
    table = get_table("rate_snapshots")
    now = datetime.now(UTC)
    total = 0

    for corridor, config in SEED_CORRIDORS.items():
        base_rate = config["base_rate"]
        volatility = config["volatility"]
        amount = config["amount"]

        print(f"Seeding {corridor}...")

        for day in range(DAYS_TO_SEED, 0, -1):
            for slot in range(SNAPSHOTS_PER_DAY):
                ts = now - timedelta(days=day) + timedelta(minutes=15 * slot)

                # Simulate rate with random walk + mean reversion
                drift = random.gauss(0, volatility * 0.01)
                rate = base_rate * (1 + drift)

                # Add a slight upward trend in the last 2 days for demo "favorable" window
                if day <= 2:
                    rate *= 1.005 + (0.003 * (2 - day))

                fees = round(random.uniform(3.0, 6.0), 2)
                recipient_amount = (amount - fees) * rate

                item = {
                    "snapshot_id": str(uuid.uuid4()),
                    "corridor": corridor,
                    "provider": "exchangerate-api",
                    "rate": str(round(rate, 4)),
                    "fees": str(fees),
                    "recipient_amount": str(round(recipient_amount, 2)),
                    "timestamp": ts.isoformat(),
                }
                table.put_item(Item=item)
                total += 1

        print(f"  {SNAPSHOTS_PER_DAY * DAYS_TO_SEED} snapshots stored for {corridor}")

    print(f"\nTotal snapshots seeded: {total}")


if __name__ == "__main__":
    seed_rate_snapshots()
