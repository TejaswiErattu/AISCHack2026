"""Recommendation service — LLM explanation generation, alert formatting,
and notification delivery.

Covers Tasks 3.4 (LLM explanations), 3.5 (alert formatting), and
3.7 (notification sending).
"""

import logging

from app.llm.bedrock import BedrockClient
from app.llm.fallbacks import FallbackTemplates
from app.llm.prompts import SYSTEM_PROMPT, build_explanation_prompt
from app.services import telegram

logger = logging.getLogger(__name__)

# Singleton Bedrock client — created lazily on first use.
_bedrock_client: BedrockClient | None = None


def _get_bedrock_client() -> BedrockClient:
    """Return (and lazily create) the shared BedrockClient instance."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client


# ──── Task 3.4 — LLM explanation generator ────


async def generate_explanation(
    literacy_level: str,
    rate_data: dict,
    baseline_data: dict,
    currency: str,
) -> str:
    """Generate a human-readable transfer recommendation using Claude.

    Parameters
    ----------
    literacy_level:
        One of ``"beginner"``, ``"intermediate"``, ``"advanced"``.
    rate_data:
        Must contain ``recipient_amount``, ``rate``, ``fees``, and
        optionally ``provider``.
    baseline_data:
        Must contain ``personal_baseline_amount``, ``pct_change``,
        ``change_amount``, ``global_baseline_amount``, and
        ``global_pct_change``.
    currency:
        ISO currency code the recipient receives (e.g. ``"INR"``).

    Returns
    -------
    str
        The LLM-generated explanation, or a deterministic fallback if
        the LLM call fails.
    """
    prompt = build_explanation_prompt(
        literacy_level=literacy_level,
        recipient_amount=rate_data["recipient_amount"],
        rate=rate_data["rate"],
        fees=rate_data.get("fees", 0.0),
        provider=rate_data.get("provider", "Wise"),
        currency=currency,
        baseline_recipient_amount=baseline_data["personal_baseline_amount"],
        pct_change=baseline_data["pct_change"],
        change_amount=baseline_data["change_amount"],
        global_baseline_amount=baseline_data["global_baseline_amount"],
        global_pct_change=baseline_data["global_pct_change"],
    )

    client = _get_bedrock_client()
    explanation = await client.invoke(
        system_prompt=SYSTEM_PROMPT,
        user_message=prompt,
    )

    if explanation:
        return explanation

    # Fallback to deterministic template
    logger.warning("LLM explanation failed — using fallback template")
    return FallbackTemplates.rate_alert(
        recipient_amount=rate_data["recipient_amount"],
        personal_baseline_amount=baseline_data["personal_baseline_amount"],
        pct_change=baseline_data["pct_change"],
        currency=currency,
    )


# ──── Task 3.5 — Alert message formatter ────


async def format_full_alert(
    rate_data: dict,
    baseline_data: dict,
    stablecoin_data: dict | None,
    literacy_level: str,
    currency: str,
) -> str:
    """Build a complete alert message for the first notification in a
    favorable window.

    Includes an LLM-generated explanation, an optional stablecoin route
    comparison, and an action-buttons hint.
    """
    explanation = await generate_explanation(
        literacy_level=literacy_level,
        rate_data=rate_data,
        baseline_data=baseline_data,
        currency=currency,
    )

    parts: list[str] = [explanation]

    # Optional stablecoin comparison block
    if stablecoin_data:
        stable_amount = stablecoin_data.get("recipient_amount", 0.0)
        stable_provider = stablecoin_data.get("provider", "Stablecoin route")
        traditional_amount = rate_data["recipient_amount"]

        diff = stable_amount - traditional_amount
        comparison = (
            f"\n--- Stablecoin comparison ---\n"
            f"{stable_provider}: {stable_amount:,.2f} {currency}\n"
            f"Traditional: {traditional_amount:,.2f} {currency}\n"
            f"Difference: {diff:+,.2f} {currency}"
        )
        parts.append(comparison)

    # Action hint (actual inline buttons are attached by send_alert_to_user)
    parts.append(
        "\nReply CONFIRM to send now, WAIT to keep monitoring, "
        "or CANCEL to dismiss."
    )

    return "\n".join(parts)


def format_short_followup(
    recipient_amount: float,
    pct_change: float,
    currency: str,
) -> str:
    """Build a short follow-up message for subsequent alerts in the same
    favorable window.
    """
    return FallbackTemplates.short_followup(
        recipient_amount=recipient_amount,
        pct_change=pct_change,
        currency=currency,
    )


# ──── Task 3.7 — Notification sender ────

# Inline keyboard rows for full alerts
_CONFIRMATION_BUTTONS: list[list[dict]] = [
    [
        {"text": "Confirm", "callback_data": "CONFIRM"},
        {"text": "Wait", "callback_data": "WAIT"},
        {"text": "Cancel", "callback_data": "CANCEL"},
    ]
]


async def send_alert_to_user(
    chat_id: str,
    alert_type: str,
    message: str,
) -> bool:
    """Deliver an alert message to the user via Telegram.

    For ``"full_alert"`` messages the Telegram inline keyboard with
    CONFIRM / WAIT / CANCEL buttons is attached.  For ``"short_followup"``
    (or any other type) a plain text message is sent.

    Returns True on success, False on failure.
    """
    try:
        if alert_type == "full_alert":
            success = await telegram.send_message_with_buttons(
                chat_id=chat_id,
                text=message,
                buttons=_CONFIRMATION_BUTTONS,
            )
        else:
            success = await telegram.send_message(
                chat_id=chat_id,
                text=message,
            )

        if success:
            logger.info(
                "Sent %s to chat_id=%s",
                alert_type,
                chat_id,
            )
        else:
            logger.warning(
                "Telegram delivery failed for %s to chat_id=%s",
                alert_type,
                chat_id,
            )
        return success

    except Exception:
        logger.exception(
            "Unexpected error sending %s to chat_id=%s",
            alert_type,
            chat_id,
        )
        return False
