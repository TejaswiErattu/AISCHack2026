"""Rule engine — threshold evaluation, payout optimization, and alert cadence.

This module contains pure computation functions (no LLM involvement) that
power the decision layer described in PRD sections 4.4, 4.5, and 8.2.
"""

import logging
from datetime import datetime, timezone

from app.db.crud import get_alert_state, update_alert_state
from app.models.schemas import AlertState

logger = logging.getLogger(__name__)


# ──── Task 3.1 — Threshold evaluation ────


def evaluate_threshold(
    current_recipient_amount: float,
    baseline_recipient_amount: float,
    threshold_pct: float,
) -> bool:
    """Return True when the current recipient amount exceeds the baseline by
    at least *threshold_pct* percent.

    >>> evaluate_threshold(8350.0, 8250.0, 1.0)
    True
    >>> evaluate_threshold(8260.0, 8250.0, 1.0)
    False
    """
    if baseline_recipient_amount <= 0:
        logger.warning(
            "Baseline recipient amount is non-positive (%.2f); "
            "cannot evaluate threshold",
            baseline_recipient_amount,
        )
        return False

    pct_change = ((current_recipient_amount - baseline_recipient_amount)
                  / baseline_recipient_amount) * 100
    return pct_change >= threshold_pct


# ──── Task 3.2 — Payout optimization ────


def compute_recipient_amount(
    amount_sent: float,
    fees: float,
    fx_rate: float,
) -> float:
    """Compute what the recipient gets after fees and FX conversion.

    Formula: (amount_sent - fees) * fx_rate
    """
    return (amount_sent - fees) * fx_rate


def compute_savings(
    current_amount: float,
    baseline_amount: float,
) -> dict:
    """Return the absolute and percentage savings vs a baseline.

    Returns a dict with keys ``absolute`` and ``percentage``.
    """
    if baseline_amount <= 0:
        logger.warning(
            "Baseline amount is non-positive (%.2f); returning zero savings",
            baseline_amount,
        )
        return {"absolute": 0.0, "percentage": 0.0}

    absolute = current_amount - baseline_amount
    percentage = (absolute / baseline_amount) * 100
    return {"absolute": absolute, "percentage": percentage}


# ──── Task 3.6 — Alert cadence ────


async def check_alert_cadence(
    user_id: str,
    corridor: str,
    is_favorable: bool,
) -> str:
    """Decide what kind of alert (if any) to send based on cadence rules.

    Returns one of:
        ``"full_alert"``      — first alert in a new favorable window, or
                                 a new window after user interaction.
        ``"short_followup"``  — subsequent alert in the same window.
        ``"no_alert"``        — conditions are not favorable.

    Side-effects: creates / updates the ``AlertState`` record in DynamoDB.
    """
    state = await get_alert_state(user_id, corridor)

    # ── Not favorable — reset the window ──
    if not is_favorable:
        if state and state.in_favorable_window:
            state.in_favorable_window = False
            state.full_alert_sent = False
            state.user_interacted_since_alert = False
            await update_alert_state(state)
            logger.debug(
                "Favorable window closed for user=%s corridor=%s",
                user_id,
                corridor,
            )
        return "no_alert"

    # ── Favorable — determine alert type ──

    # First time we see this user/corridor — create fresh state
    if state is None:
        state = AlertState(
            user_id=user_id,
            corridor=corridor,
            in_favorable_window=True,
            full_alert_sent=True,
            last_alert_at=datetime.now(timezone.utc),
            user_interacted_since_alert=False,
        )
        await update_alert_state(state)
        logger.info(
            "New favorable window — full_alert for user=%s corridor=%s",
            user_id,
            corridor,
        )
        return "full_alert"

    # No full alert sent yet in this window
    if not state.full_alert_sent:
        state.in_favorable_window = True
        state.full_alert_sent = True
        state.last_alert_at = datetime.now(timezone.utc)
        state.user_interacted_since_alert = False
        await update_alert_state(state)
        logger.info(
            "First full_alert in window for user=%s corridor=%s",
            user_id,
            corridor,
        )
        return "full_alert"

    # Full alert already sent, but user has interacted → new window
    if state.user_interacted_since_alert:
        state.in_favorable_window = True
        state.full_alert_sent = True
        state.last_alert_at = datetime.now(timezone.utc)
        state.user_interacted_since_alert = False
        await update_alert_state(state)
        logger.info(
            "User interacted — new full_alert for user=%s corridor=%s",
            user_id,
            corridor,
        )
        return "full_alert"

    # Full alert already sent, no user interaction → short followup
    state.last_alert_at = datetime.now(timezone.utc)
    await update_alert_state(state)
    logger.debug(
        "short_followup for user=%s corridor=%s",
        user_id,
        corridor,
    )
    return "short_followup"


async def mark_user_interaction(user_id: str, corridor: str) -> None:
    """Record that the user has interacted since the last full alert.

    Called when the user presses CONFIRM / WAIT / CANCEL, asks a question,
    or changes preferences — any action that signals engagement.
    """
    state = await get_alert_state(user_id, corridor)
    if state is None:
        logger.debug(
            "No alert state found for user=%s corridor=%s; nothing to mark",
            user_id,
            corridor,
        )
        return

    state.user_interacted_since_alert = True
    await update_alert_state(state)
    logger.debug(
        "Marked user interaction for user=%s corridor=%s",
        user_id,
        corridor,
    )
