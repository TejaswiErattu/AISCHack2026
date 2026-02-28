"""Bot command handlers (/start, /help, /status, /reset)."""

import logging

from app.models.schemas import OnboardingStep

logger = logging.getLogger(__name__)

# Callback data values for reset confirmation buttons
RESET_CONFIRM = "RESET_CONFIRM"
RESET_CANCEL = "RESET_CANCEL"


async def handle_command(chat_id: str, user: dict, command: str) -> None:
    """Dispatch a recognised bot command to the appropriate handler."""
    handlers = {
        "/start": _handle_start,
        "/help": _handle_help,
        "/status": _handle_status,
        "/reset": _handle_reset,
    }
    handler = handlers.get(command)
    if handler:
        await handler(chat_id, user)
    else:
        from app.services.telegram import send_message

        await send_message(chat_id, "Unknown command. Try /help for a list of commands.")


async def _handle_start(chat_id: str, user: dict) -> None:
    from app.services.telegram import send_message

    await send_message(
        chat_id,
        "Welcome back! You're already set up. Use /help to see available commands.",
    )


async def _handle_help(chat_id: str, user: dict) -> None:
    from app.services.telegram import send_message

    await send_message(
        chat_id,
        (
            "*Available commands:*\n"
            "/start — Welcome message\n"
            "/help — Show this list\n"
            "/status — View your profile and preferences\n"
            "/reset — Reset your profile and start over"
        ),
    )


async def _handle_status(chat_id: str, user: dict) -> None:
    from app.services.telegram import send_message

    step = user.get("onboarding_step", "unknown")
    lang = user.get("language", "en")
    await send_message(
        chat_id,
        f"*Your status:*\nLanguage: {lang}\nOnboarding: {step}",
    )


async def _handle_reset(chat_id: str, user: dict) -> None:
    """Send a confirmation prompt with YES/NO buttons."""
    from app.services.telegram import send_message_with_buttons

    buttons = [
        [
            {"text": "Yes, reset", "callback_data": RESET_CONFIRM},
            {"text": "Cancel", "callback_data": RESET_CANCEL},
        ]
    ]
    await send_message_with_buttons(
        chat_id,
        (
            "Are you sure you want to reset? This will erase your profile and "
            "preferences, and you'll go through setup again.\n\n"
            "Your transfer history will be kept."
        ),
        buttons,
    )


async def handle_reset_confirm(chat_id: str, user: dict) -> None:
    """Perform the actual reset: delete profile, prefs, alerts, restart onboarding."""
    from app.db.crud import (
        create_preferences,
        create_profile,
        delete_alert_states,
        delete_preferences,
        delete_profile,
        get_profile_by_user,
        get_user_by_telegram_id,
        update_user,
    )
    from app.llm.fallbacks import FallbackTemplates
    from app.services.telegram import send_message

    user_id = user.get("user_id")
    if not user_id:
        await send_message(chat_id, "Something went wrong. Please try again.")
        return

    # Delete profile
    profile = await get_profile_by_user(user_id)
    if profile:
        await delete_profile(profile.profile_id)

    # Delete preferences
    await delete_preferences(user_id)

    # Delete alert states
    await delete_alert_states(user_id)

    # Reset onboarding step and language to defaults
    user_obj = await get_user_by_telegram_id(chat_id)
    if user_obj:
        user_obj.onboarding_step = OnboardingStep.LANGUAGE
        user_obj.language = "en"
        await update_user(user_obj)

    # Create fresh profile and preferences for the new onboarding run
    await create_profile(user_id)
    await create_preferences(user_id)

    logger.info("User %s reset their profile (chat_id=%s)", user_id, chat_id)

    await send_message(chat_id, "Your profile has been reset. Let's start fresh!")
    question = FallbackTemplates.onboarding_question(OnboardingStep.LANGUAGE)
    await send_message(chat_id, question)


async def handle_reset_cancel(chat_id: str, user: dict) -> None:
    """Cancel the reset — no changes made."""
    from app.services.telegram import send_message

    await send_message(chat_id, "Reset cancelled. Nothing was changed.")
