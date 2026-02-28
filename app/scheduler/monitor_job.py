"""Scheduled monitoring job — runs every 15 minutes.

Entry point for the rate monitoring cycle. Can be invoked by:
- AWS Lambda + EventBridge (via handler in app.main)
- Local APScheduler for development
- Manual trigger via CLI
"""

import logging

logger = logging.getLogger(__name__)


async def run_monitor_job() -> dict:
    """Execute one monitoring cycle.

    1. Fetch all active corridors
    2. For each corridor: fetch FX rate, store snapshot
    3. For each user in that corridor: check threshold, send alerts
    """
    from app.db import crud
    from app.services.rate_monitor import (
        compute_personal_baseline,
        fetch_fx_rate,
        store_snapshot,
    )

    summary = {"corridors_checked": 0, "snapshots_stored": 0, "alerts_triggered": 0}

    corridors = await crud.get_all_active_corridors()
    if not corridors:
        logger.info("No active corridors to monitor")
        return summary

    for corridor_info in corridors:
        corridor = corridor_info["corridor"]
        parts = corridor.split("_")
        if len(parts) != 2:
            logger.warning("Invalid corridor format: %s", corridor)
            continue

        base_currency, target_currency = parts
        amount = corridor_info.get("average_amount", 500.0)

        # Fetch current rate
        rate_data = await fetch_fx_rate(base_currency, target_currency)
        if not rate_data:
            logger.warning("Failed to fetch rate for %s", corridor)
            continue

        summary["corridors_checked"] += 1

        # Store snapshot
        snapshot_id = await store_snapshot(
            corridor=corridor,
            rate=rate_data["rate"],
            fees=0.0,
            amount_sent=float(amount),
        )
        if snapshot_id:
            summary["snapshots_stored"] += 1

        # Compute baseline
        baseline = await compute_personal_baseline(corridor)

        # Check thresholds and send alerts for all users in this corridor
        alerts = await _check_and_alert_corridor(
            corridor=corridor,
            rate=rate_data["rate"],
            amount_sent=float(amount),
            baseline=baseline,
        )
        summary["alerts_triggered"] += alerts

    logger.info("Monitoring cycle complete: %s", summary)
    return summary


async def _check_and_alert_corridor(
    corridor: str,
    rate: float,
    amount_sent: float,
    baseline: dict | None,
) -> int:
    """Check thresholds and send alerts for all users in a corridor."""
    from app.db import crud
    from app.services.decision_engine import (
        check_alert_cadence,
        compute_recipient_amount,
        compute_savings,
        evaluate_threshold,
    )
    from app.services.recommendation import (
        format_full_alert,
        format_short_followup,
        send_alert_to_user,
    )
    from app.services.stablecoin import compute_stablecoin_route

    if not baseline:
        return 0

    alerts_sent = 0
    current_recipient = compute_recipient_amount(amount_sent, 0.0, rate)

    # Get all profiles for this corridor
    table = crud.get_table("remittance_profiles")
    resp = table.scan(
        FilterExpression="corridor = :c",
        ExpressionAttributeValues={":c": corridor},
    )
    profiles = resp.get("Items", [])

    for profile in profiles:
        user_id = profile.get("user_id")
        if not user_id:
            continue

        user = await crud.get_user(user_id)
        if not user:
            continue

        prefs = await crud.get_preferences(user_id)
        threshold_pct = float(prefs.alert_threshold_pct) if prefs else 1.0

        baseline_amount = baseline["avg_recipient_amount"]
        is_favorable = evaluate_threshold(current_recipient, baseline_amount, threshold_pct)

        alert_type = await check_alert_cadence(user_id, corridor, is_favorable)
        if alert_type == "no_alert":
            continue

        savings = compute_savings(current_recipient, baseline_amount)
        literacy = prefs.financial_literacy_level.value if prefs else "beginner"
        parts = corridor.split("_")
        currency = parts[1] if len(parts) == 2 else "INR"

        # Get stablecoin comparison
        stablecoin_data = await compute_stablecoin_route(amount_sent, currency.lower())

        rate_data = {
            "recipient_amount": current_recipient,
            "rate": rate,
            "fees": 0.0,
            "provider": "exchangerate-api",
        }
        baseline_data = {
            "avg_recipient_amount": baseline_amount,
            "pct_change": savings["percentage"],
            "change_amount": savings["absolute"],
            "global_baseline_amount": baseline_amount,  # fallback
            "global_pct_change": savings["percentage"],
        }

        if alert_type == "full_alert":
            message = await format_full_alert(
                rate_data, baseline_data, stablecoin_data, literacy, currency
            )
        else:
            message = format_short_followup(current_recipient, savings["percentage"], currency)

        sent = await send_alert_to_user(user.telegram_chat_id, alert_type, message)
        if sent:
            alerts_sent += 1

    return alerts_sent
