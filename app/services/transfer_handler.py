"""Transfer confirmation flow — handles CONFIRM / WAIT / CANCEL commands."""

import logging
import uuid

from app.db import crud
from app.models.schemas import Transfer, TransferStatus

logger = logging.getLogger(__name__)


async def handle_confirmation(user_id: str, chat_id: str, action: str) -> None:
    """Handle user's transfer decision: CONFIRM, WAIT, or CANCEL."""
    from app.services.telegram import send_message

    action = action.strip().upper()

    if action == "CONFIRM":
        await _handle_confirm(user_id, chat_id)
    elif action == "WAIT":
        await send_message(chat_id, "Got it — I'll keep monitoring and let you know if conditions improve.")
        await crud.mark_user_interaction(user_id)
    elif action == "CANCEL":
        await send_message(chat_id, "Transfer cancelled. I'll continue monitoring rates for you.")
        await crud.mark_user_interaction(user_id)
    else:
        await send_message(chat_id, "I didn't understand that. Reply CONFIRM, WAIT, or CANCEL.")


async def _handle_confirm(user_id: str, chat_id: str) -> None:
    """Execute transfer via Wise sandbox or show recommendation-only message."""
    from app.services.decision_engine import compute_recipient_amount, compute_savings
    from app.services.rate_monitor import compute_personal_baseline, fetch_fx_rate
    from app.services.recommendation import generate_explanation
    from app.services.telegram import send_message
    from app.services.wise_adapter import create_quote, create_transfer

    profile = await crud.get_profile_by_user(user_id)
    if not profile:
        await send_message(chat_id, "Please complete onboarding first with /start.")
        return

    prefs = await crud.get_preferences(user_id)

    # Check for duplicate in-progress transfers
    existing = await crud.get_user_transfers(user_id)
    pending = [t for t in existing if t.status in (TransferStatus.PENDING, TransferStatus.PROCESSING)]
    if pending:
        await send_message(
            chat_id,
            f"You already have a transfer in progress (ID: {pending[0].transfer_id[:8]}...). "
            "Please wait for it to complete before starting a new one.",
        )
        return

    if not profile.execution_enabled:
        # Recommendation-only mode for non-US→India corridors
        await _handle_recommendation_only(profile, prefs, chat_id)
        return

    # Execution mode: US → India via Wise sandbox
    user = await crud.get_user(user_id)
    if not user:
        return

    parts = profile.corridor.split("_")
    if len(parts) != 2:
        await send_message(chat_id, "Invalid corridor configuration. Please update your profile.")
        return

    base_currency, target_currency = parts
    amount = profile.average_amount

    # Get current rate
    rate_data = await fetch_fx_rate(base_currency, target_currency)
    if not rate_data:
        await send_message(chat_id, "Unable to fetch current rates. Please try again shortly.")
        return

    rate = rate_data["rate"]
    recipient_amount = compute_recipient_amount(amount, 0.0, rate)

    # Create transfer record
    transfer = Transfer(
        transfer_id=str(uuid.uuid4()),
        user_id=user_id,
        provider="wise_sandbox",
        amount_sent=amount,
        currency_from=base_currency,
        currency_to=target_currency,
        fx_rate=rate,
        fees=0.0,
        recipient_amount=recipient_amount,
        status=TransferStatus.PENDING,
    )
    await crud.create_transfer(transfer)

    # Try Wise sandbox execution
    from app.services.wise_adapter import is_configured

    if not is_configured():
        # Fall back to mock provider
        from app.services.mock_wise import create_quote as mock_quote, create_transfer as mock_create
        quote = await mock_quote(base_currency, target_currency, amount)
        quote_id = quote.get("id", "")
        wise_transfer = await mock_create(quote_id)
    else:
        quote = await create_quote(base_currency, target_currency, amount)
        wise_transfer = None
        if quote:
            quote_id = quote.get("id", "")
            wise_transfer = await create_transfer(quote_id, 0)

    if wise_transfer:
        if wise_transfer:
            transfer.provider_tx_id = str(wise_transfer.get("id", ""))
            transfer.status = TransferStatus.CREATED
            await crud.update_transfer(transfer)

            # Compute savings
            baseline = await compute_personal_baseline(profile.corridor)
            baseline_amount = baseline["avg_recipient_amount"] if baseline else recipient_amount
            savings = compute_savings(recipient_amount, baseline_amount)

            await send_message(
                chat_id,
                f"Transfer initiated!\n\n"
                f"Transfer ID: `{transfer.transfer_id[:8]}`\n"
                f"Amount: {amount} {base_currency}\n"
                f"Recipient gets: {recipient_amount:,.2f} {target_currency}\n"
                f"Rate: {rate:.4f}\n\n"
                f"Savings vs your average: {savings['absolute']:+,.2f} {target_currency} "
                f"({savings['percentage']:+.1f}%)\n\n"
                f"I'll update you on the transfer status.",
            )

            # Store savings record
            await crud.store_savings_record({
                "transfer_id": transfer.transfer_id,
                "user_id": user_id,
                "baseline_rate": str(baseline["avg_rate"]) if baseline else str(rate),
                "optimized_rate": str(rate),
                "personal_savings": str(savings["absolute"]),
                "global_savings": str(savings["absolute"]),
            })
            return

    # Wise call failed — still record the transfer as pending
    transfer.status = TransferStatus.FAILED
    await crud.update_transfer(transfer)
    await send_message(
        chat_id,
        "Transfer could not be completed via Wise sandbox right now. "
        "The rate and recommendation have been saved. Please try again later.",
    )


async def _handle_recommendation_only(profile, prefs, chat_id: str) -> None:
    """For corridors without execution support, provide recommendation only."""
    from app.services.telegram import send_message

    await send_message(
        chat_id,
        f"Transfer execution is not yet available for the "
        f"{profile.sender_country} → {profile.recipient_country} corridor.\n\n"
        f"I recommend using a provider like Wise, Remitly, or your bank "
        f"to send {profile.average_amount} {profile.corridor.split('_')[0]} now "
        f"while conditions are favorable.\n\n"
        f"I'll continue monitoring rates and alerting you to opportunities!",
    )


async def mark_user_interaction(user_id: str) -> None:
    """Mark that a user has interacted, which resets alert cadence."""
    from app.services.decision_engine import mark_user_interaction as _mark

    profile = await crud.get_profile_by_user(user_id)
    if profile and profile.corridor:
        await _mark(user_id, profile.corridor)


async def get_transfer_status_for_user(user_id: str, chat_id: str) -> None:
    """Report transfer status to user."""
    from app.services.telegram import send_message

    transfers = await crud.get_user_transfers(user_id)
    if not transfers:
        await send_message(chat_id, "You don't have any transfers yet.")
        return

    latest = transfers[-1]
    await send_message(
        chat_id,
        f"Latest transfer:\n"
        f"ID: `{latest.transfer_id[:8]}`\n"
        f"Amount: {latest.amount_sent} {latest.currency_from}\n"
        f"Recipient gets: {latest.recipient_amount:,.2f} {latest.currency_to}\n"
        f"Status: {latest.status.value}\n"
        f"Rate: {latest.fx_rate:.4f}",
    )
