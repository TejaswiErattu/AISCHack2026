"""Telegram bot service — message sending and update routing."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


# ---------------------------------------------------------------------------
# Helpers: extract fields from Telegram update dicts
# ---------------------------------------------------------------------------


def extract_chat_id(update: dict) -> str | None:
    """Extract chat_id from a Telegram update.

    Handles both regular messages and callback queries.
    """
    if "callback_query" in update:
        return str(update["callback_query"]["message"]["chat"]["id"])
    if "message" in update:
        return str(update["message"]["chat"]["id"])
    return None


def extract_message_text(update: dict) -> str | None:
    """Extract the user-facing text from a Telegram update.

    For callback queries the ``data`` field is returned (e.g. CONFIRM).
    For regular messages the ``text`` field is returned.
    """
    if "callback_query" in update:
        return update["callback_query"].get("data")
    if "message" in update:
        return update["message"].get("text")
    return None


# ---------------------------------------------------------------------------
# Outbound: send messages to users
# ---------------------------------------------------------------------------


async def send_message(
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> bool:
    """Send a plain text message to a Telegram chat.

    Returns True on success, False otherwise.
    """
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Telegram sendMessage HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Telegram sendMessage request failed: %s", exc)
    return False


async def send_message_with_buttons(
    chat_id: str,
    text: str,
    buttons: list[list[dict]],
    parse_mode: str = "Markdown",
) -> bool:
    """Send a message with an inline keyboard (e.g. CONFIRM / WAIT / CANCEL).

    ``buttons`` should be a list of rows, where each row is a list of dicts
    with ``text`` and ``callback_data`` keys, matching Telegram's
    InlineKeyboardButton schema.

    Example::

        buttons = [
            [
                {"text": "Confirm", "callback_data": "CONFIRM"},
                {"text": "Wait",    "callback_data": "WAIT"},
                {"text": "Cancel",  "callback_data": "CANCEL"},
            ]
        ]

    Returns True on success, False otherwise.
    """
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {
            "inline_keyboard": buttons,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Telegram sendMessage (buttons) HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Telegram sendMessage (buttons) request failed: %s", exc)
    return False


# ---------------------------------------------------------------------------
# Inbound: route incoming updates
# ---------------------------------------------------------------------------

# Callback-query values that map to transfer confirmation actions
_CONFIRMATION_ACTIONS = {"CONFIRM", "WAIT", "CANCEL"}

# Recognised bot commands
_COMMANDS = {"/start", "/help", "/status", "/reset"}

# Callback-query values for the reset confirmation flow
_RESET_ACTIONS = {"RESET_CONFIRM", "RESET_CANCEL"}


async def handle_update(update: dict) -> None:
    """Main router for incoming Telegram updates.

    Extracts the chat_id and message text, then dispatches to the appropriate
    handler based on:
      1. Whether the user exists in the database.
      2. The user's current onboarding step.
      3. Bot commands (/start, /help, /status).
      4. Confirmation button presses (CONFIRM / WAIT / CANCEL).
      5. Preference-update patterns.
      6. Fallback to the general LLM message handler.
    """
    chat_id = extract_chat_id(update)
    text = extract_message_text(update)

    if chat_id is None:
        logger.warning("Could not extract chat_id from update: %s", update.get("update_id"))
        return

    try:
        # --- lazy imports to avoid circular dependencies ---
        from app.db.crud import get_user_by_telegram_id
        from app.models.schemas import OnboardingStep

        # Look up user
        user = await get_user_by_telegram_id(chat_id)

        # 1. New user — kick off onboarding
        if user is None:
            from app.services.onboarding import start_onboarding  # type: ignore[import-untyped]

            await start_onboarding(chat_id)
            return

        # 1b. /reset works at any point (even mid-onboarding)
        if text and text.strip().lower() == "/reset":
            from app.services.commands import handle_command  # type: ignore[import-untyped]

            await handle_command(chat_id, user, "/reset")
            return

        # 1c. Reset confirmation callbacks
        is_callback = "callback_query" in update
        if is_callback and text in _RESET_ACTIONS:
            from app.services.commands import (  # type: ignore[import-untyped]
                handle_reset_cancel,
                handle_reset_confirm,
            )

            if text == "RESET_CONFIRM":
                await handle_reset_confirm(chat_id, user)
            else:
                await handle_reset_cancel(chat_id, user)
            return

        # 2. User mid-onboarding
        if user.onboarding_step and user.onboarding_step != OnboardingStep.COMPLETE:
            from app.services.onboarding import handle_onboarding_step  # type: ignore[import-untyped]

            await handle_onboarding_step(chat_id, user, text)
            return

        # From here on the user is fully onboarded.

        # 3. Handle callback queries for transfer confirmation
        if is_callback and text and text.upper() in _CONFIRMATION_ACTIONS:
            from app.services.transfer import handle_confirmation  # type: ignore[import-untyped]

            await handle_confirmation(chat_id, user, text.upper())
            return

        # 4. Bot commands
        if text and text.strip().lower() in _COMMANDS:
            from app.services.commands import handle_command  # type: ignore[import-untyped]

            await handle_command(chat_id, user, text.strip().lower())
            return

        # 5. Transfer confirmation keywords sent as plain text
        if text and text.strip().upper() in _CONFIRMATION_ACTIONS:
            from app.services.transfer import handle_confirmation  # type: ignore[import-untyped]

            await handle_confirmation(chat_id, user, text.strip().upper())
            return

        # 6. Preference update pattern (e.g. "set threshold 2%")
        if text and _looks_like_preference_update(text):
            from app.services.preferences import handle_preference_update  # type: ignore[import-untyped]

            await handle_preference_update(chat_id, user, text)
            return

        # 7. Fallback — general LLM intent classification
        from app.services.message_handler import handle_general_message  # type: ignore[import-untyped]

        await handle_general_message(chat_id, user, text)

    except Exception:
        logger.exception("Unhandled error processing update for chat_id=%s", chat_id)
        await send_message(chat_id, "Something went wrong. Please try again later.")


def _looks_like_preference_update(text: str) -> bool:
    """Simple heuristic to detect preference-update intent.

    Returns True if the message starts with common preference keywords.
    This is a lightweight pre-filter; the preference handler does the real
    parsing.
    """
    lower = text.strip().lower()
    prefixes = ("set ", "change ", "update ", "threshold ", "alert ")
    return any(lower.startswith(p) for p in prefixes)
