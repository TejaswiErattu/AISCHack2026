"""Onboarding conversation state machine for RemitAgent.

Guides new users through a 5-step onboarding flow:
  1. LANGUAGE   -- preferred language
  2. LITERACY   -- financial literacy level
  3. SENDER_COUNTRY   -- country the user sends from
  4. RECIPIENT_COUNTRY -- country the recipient is in
  5. AMOUNT     -- typical transfer amount

After all steps, a profile summary is shown for confirmation (CONFIRM step).
On confirmation the user's onboarding is marked COMPLETE and rate monitoring
begins for their corridor.
"""

import json
import logging
import re

from app.db.crud import (
    create_preferences,
    create_profile,
    create_user,
    get_preferences,
    get_profile_by_user,
    update_profile,
    update_user,
)
from app.llm.bedrock import BedrockClient
from app.llm.fallbacks import FallbackTemplates
from app.llm.prompts import ONBOARDING_EXTRACTION_PROMPT, SYSTEM_PROMPT
from app.models.schemas import LiteracyLevel, OnboardingStep, User
from app.services.telegram import send_message

logger = logging.getLogger(__name__)

# ──── Constants ────

COUNTRY_TO_CURRENCY: dict[str, str] = {
    "US": "USD",
    "IN": "INR",
    "PH": "PHP",
    "MX": "MXN",
    "GB": "GBP",
    "AE": "AED",
    "CA": "CAD",
    "AU": "AUD",
    "SG": "SGD",
    "DE": "EUR",
    "FR": "EUR",
}

# Ordered list used to advance through onboarding steps.
_STEP_ORDER: list[OnboardingStep] = [
    OnboardingStep.LANGUAGE,
    OnboardingStep.LITERACY,
    OnboardingStep.SENDER_COUNTRY,
    OnboardingStep.RECIPIENT_COUNTRY,
    OnboardingStep.AMOUNT,
    OnboardingStep.CONFIRM,
    OnboardingStep.COMPLETE,
]

# Words that count as positive confirmation at the CONFIRM step.
_CONFIRM_WORDS = {"yes", "y", "confirm", "correct", "ok", "looks good", "lgtm"}

# Words that indicate the user wants to change something at the CONFIRM step.
_EDIT_WORDS = {"edit", "change", "no", "wrong", "update", "fix", "redo"}

# Shared LLM client instance (module-level singleton).
_llm = BedrockClient()


# ──── Public API ────


async def start_onboarding(chat_id: str) -> None:
    """Create a new user record and send the first onboarding question.

    This is the entry point when a previously unseen Telegram chat_id sends
    a message for the first time.
    """
    logger.info("Starting onboarding for chat_id=%s", chat_id)

    try:
        user = await create_user(telegram_chat_id=chat_id)
        await create_profile(user.user_id)
        await create_preferences(user.user_id)

        question = FallbackTemplates.onboarding_question(OnboardingStep.LANGUAGE)
        await send_message(chat_id, question)

        logger.info(
            "Onboarding initiated for user_id=%s, chat_id=%s",
            user.user_id,
            chat_id,
        )
    except Exception:
        logger.exception("Failed to start onboarding for chat_id=%s", chat_id)
        await send_message(
            chat_id,
            "Sorry, something went wrong while setting up your account. "
            "Please try again with /start.",
        )


async def handle_onboarding_step(
    user: User,
    message_text: str,
    chat_id: str,
) -> None:
    """Main dispatch for processing a user's answer during onboarding.

    1. Parse the user's free-text answer via LLM structured extraction.
    2. Fall back to simple heuristic parsing if the LLM returns nothing.
    3. Update the appropriate user/profile field.
    4. Advance to the next onboarding step.
    5. Send the next question (or profile summary at CONFIRM).

    Args:
        user: The current ``User`` model (with ``onboarding_step`` set).
        message_text: Raw text from the user's Telegram message.
        chat_id: Telegram chat ID for sending replies.
    """
    current_step = user.onboarding_step

    if current_step == OnboardingStep.COMPLETE:
        logger.debug("User %s already completed onboarding; ignoring.", user.user_id)
        return

    if current_step == OnboardingStep.CONFIRM:
        await _handle_confirmation_step(user, message_text, chat_id)
        return

    logger.info(
        "Processing onboarding step=%s for user_id=%s",
        current_step.value,
        user.user_id,
    )

    # ── 1. Parse the answer ──
    extracted = await _extract_answer(current_step, message_text)

    if extracted is None:
        # Could not parse -- ask the user to try again.
        fallback_q = FallbackTemplates.onboarding_question(current_step)
        await send_message(
            chat_id,
            "I didn't quite catch that. Let me ask again:\n\n" + fallback_q,
        )
        return

    # ── 2. Persist the parsed value ──
    try:
        await _apply_answer(user, current_step, extracted)
    except ValueError as exc:
        logger.warning(
            "Invalid answer for step=%s, user_id=%s: %s",
            current_step.value,
            user.user_id,
            exc,
        )
        await send_message(
            chat_id,
            f"That doesn't look right: {exc}\n\n"
            + FallbackTemplates.onboarding_question(current_step),
        )
        return

    # ── 3. Advance to next step ──
    next_step = _next_step(current_step)
    user.onboarding_step = next_step
    await update_user(user)

    # ── 4. Send the next question or profile summary ──
    if next_step == OnboardingStep.CONFIRM:
        await show_profile_summary(user, chat_id)
    else:
        question = await _generate_question(next_step)
        await send_message(chat_id, question)

    logger.info(
        "Advanced user_id=%s from %s to %s",
        user.user_id,
        current_step.value,
        next_step.value,
    )


async def show_profile_summary(user: User, chat_id: str) -> None:
    """Format and send the onboarding profile summary for user confirmation.

    Gathers data from the User, RemittanceProfile, and UserPreferences
    records and renders them into a readable summary via
    ``FallbackTemplates.profile_summary``.
    """
    profile = await get_profile_by_user(user.user_id)
    prefs = await get_preferences(user.user_id)

    profile_dict: dict = {
        "language": user.language,
        "sender_country": profile.sender_country if profile else "Not set",
        "recipient_country": profile.recipient_country if profile else "Not set",
        "average_amount": float(profile.average_amount) if profile else 0.0,
        "financial_literacy_level": (
            prefs.financial_literacy_level.value if prefs else "beginner"
        ),
    }

    summary_text = FallbackTemplates.profile_summary(profile_dict)
    await send_message(chat_id, summary_text)


# ──── Internal helpers ────


async def _extract_answer(
    step: OnboardingStep,
    message_text: str,
) -> str | float | None:
    """Use the LLM to extract a structured value from the user's message.

    Falls back to simple regex / keyword matching when the LLM is
    unavailable or returns unparseable output.

    Returns the extracted value (str or float) or ``None`` if parsing fails.
    """
    field_name = _step_to_field(step)

    # ── Try LLM extraction ──
    prompt = (
        f"{ONBOARDING_EXTRACTION_PROMPT}\n\n"
        f"Current onboarding step: {step.value}\n"
        f"Field to extract: {field_name}\n"
        f"User's message: {message_text}"
    )
    try:
        raw = await _llm.extract_structured(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
        )
        if raw:
            parsed = _parse_llm_json(raw)
            if parsed is not None:
                return parsed
    except Exception:
        logger.exception("LLM extraction failed for step=%s", step.value)

    # ── Fallback: simple parsing ──
    return _simple_parse(step, message_text)


def _parse_llm_json(raw: str) -> str | float | None:
    """Attempt to extract the ``value`` key from the LLM's JSON response.

    Returns ``None`` when the JSON is invalid or ``value`` is null.
    """
    # Strip markdown code fences if present.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("LLM returned non-JSON: %s", raw[:200])
        return None

    value = data.get("value")
    if value is None:
        reason = data.get("reason", "unknown")
        logger.debug("LLM could not extract value: %s", reason)
        return None

    return value


def _simple_parse(step: OnboardingStep, text: str) -> str | float | None:
    """Heuristic fallback parser when LLM extraction is unavailable.

    Covers the most common cases for each onboarding step.
    """
    text = text.strip()

    if step == OnboardingStep.LANGUAGE:
        return _parse_language(text)

    if step == OnboardingStep.LITERACY:
        return _parse_literacy(text)

    if step == OnboardingStep.SENDER_COUNTRY:
        return _parse_country(text)

    if step == OnboardingStep.RECIPIENT_COUNTRY:
        return _parse_country(text)

    if step == OnboardingStep.AMOUNT:
        return _parse_amount(text)

    return None


def _parse_language(text: str) -> str | None:
    """Map common language names and codes to ISO 639-1."""
    mapping = {
        "english": "en",
        "spanish": "es",
        "hindi": "hi",
        "french": "fr",
        "tagalog": "tl",
        "filipino": "tl",
        "arabic": "ar",
        "german": "de",
        "chinese": "zh",
        "mandarin": "zh",
        "portuguese": "pt",
    }
    lower = text.lower().strip()
    # Direct ISO code (2 chars)
    if len(lower) == 2 and lower.isalpha():
        return lower
    return mapping.get(lower)


def _parse_literacy(text: str) -> str | None:
    """Map user descriptions to a LiteracyLevel value."""
    lower = text.lower().strip()
    if lower in {"1", "beginner", "simple", "easy", "basic"}:
        return LiteracyLevel.BEGINNER.value
    if lower in {"2", "intermediate", "some knowledge", "medium", "moderate"}:
        return LiteracyLevel.INTERMEDIATE.value
    if lower in {"3", "advanced", "expert", "technical", "pro"}:
        return LiteracyLevel.ADVANCED.value
    return None


def _parse_country(text: str) -> str | None:
    """Map common country names to ISO 3166-1 alpha-2 codes."""
    mapping = {
        "united states": "US",
        "usa": "US",
        "us": "US",
        "america": "US",
        "india": "IN",
        "philippines": "PH",
        "mexico": "MX",
        "united kingdom": "GB",
        "uk": "GB",
        "uae": "AE",
        "united arab emirates": "AE",
        "canada": "CA",
        "australia": "AU",
        "singapore": "SG",
        "germany": "DE",
        "france": "FR",
    }
    lower = text.lower().strip()
    # Direct alpha-2 code
    if len(lower) == 2 and lower.isalpha():
        return lower.upper()
    return mapping.get(lower)


def _parse_amount(text: str) -> float | None:
    """Extract a numeric amount from free text, stripping currency symbols."""
    # Remove common currency symbols and words
    cleaned = re.sub(r"[$$£€₹₱]", "", text)
    cleaned = re.sub(r"\b(?:USD|GBP|EUR|INR|PHP|MXN|AED|CAD|AUD|SGD)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if match:
        return float(match.group(1))
    return None


def _step_to_field(step: OnboardingStep) -> str:
    """Map an onboarding step to the field name the LLM should extract."""
    return {
        OnboardingStep.LANGUAGE: "language",
        OnboardingStep.LITERACY: "literacy",
        OnboardingStep.SENDER_COUNTRY: "sender_country",
        OnboardingStep.RECIPIENT_COUNTRY: "recipient_country",
        OnboardingStep.AMOUNT: "amount",
    }.get(step, step.value)


async def _apply_answer(
    user: User,
    step: OnboardingStep,
    value: str | float,
) -> None:
    """Persist the extracted answer to the appropriate database record.

    Raises ``ValueError`` if the value is invalid for the given step.
    """
    if step == OnboardingStep.LANGUAGE:
        user.language = str(value)
        await update_user(user)

    elif step == OnboardingStep.LITERACY:
        literacy_str = str(value).lower()
        try:
            literacy = LiteracyLevel(literacy_str)
        except ValueError:
            raise ValueError(
                f"'{value}' is not a valid literacy level. "
                "Please choose beginner, intermediate, or advanced."
            )
        prefs = await get_preferences(user.user_id)
        if prefs:
            prefs.financial_literacy_level = literacy
            from app.db.crud import update_preferences
            await update_preferences(prefs)

    elif step == OnboardingStep.SENDER_COUNTRY:
        country_code = str(value).upper()
        profile = await get_profile_by_user(user.user_id)
        if profile:
            profile.sender_country = country_code
            # Recompute corridor and execution_enabled if recipient is already set
            if profile.recipient_country:
                _update_corridor(profile)
            await update_profile(profile)

    elif step == OnboardingStep.RECIPIENT_COUNTRY:
        country_code = str(value).upper()
        profile = await get_profile_by_user(user.user_id)
        if profile:
            profile.recipient_country = country_code
            # Recompute corridor and execution_enabled now that both countries are set
            if profile.sender_country:
                _update_corridor(profile)
            await update_profile(profile)

    elif step == OnboardingStep.AMOUNT:
        amount = float(value)
        if amount <= 0:
            raise ValueError("Amount must be a positive number.")
        profile = await get_profile_by_user(user.user_id)
        if profile:
            profile.average_amount = amount
            await update_profile(profile)

    else:
        logger.warning("No apply handler for step=%s", step.value)


def _update_corridor(profile) -> None:
    """Recompute corridor string and execution_enabled flag on a profile.

    Sets ``execution_enabled = True`` only for the USD -> INR corridor.
    """
    sender_currency = COUNTRY_TO_CURRENCY.get(profile.sender_country, "")
    recipient_currency = COUNTRY_TO_CURRENCY.get(profile.recipient_country, "")

    if sender_currency and recipient_currency:
        profile.corridor = f"{sender_currency}_{recipient_currency}"
        profile.execution_enabled = profile.corridor == "USD_INR"
    else:
        profile.corridor = ""
        profile.execution_enabled = False


def _next_step(current: OnboardingStep) -> OnboardingStep:
    """Return the onboarding step that follows ``current``."""
    try:
        idx = _STEP_ORDER.index(current)
        return _STEP_ORDER[idx + 1]
    except (ValueError, IndexError):
        return OnboardingStep.COMPLETE


async def _handle_confirmation_step(
    user: User,
    message_text: str,
    chat_id: str,
) -> None:
    """Handle the user's reply at the CONFIRM step.

    - Positive confirmation -> complete onboarding.
    - Edit request -> ask what to change, loop back to the relevant step.
    - Anything else -> re-prompt.
    """
    lower = message_text.strip().lower()

    if lower in _CONFIRM_WORDS:
        await _complete_onboarding(user, chat_id)
        return

    if any(word in lower for word in _EDIT_WORDS):
        await send_message(
            chat_id,
            "Sure! What would you like to change?\n\n"
            "You can say things like:\n"
            "- \"change language to Spanish\"\n"
            "- \"change sender country to UK\"\n"
            "- \"change amount to 1000\"\n"
            "- \"change level to advanced\"",
        )
        # Route the next message back through the edit handler by moving
        # the step back. We keep the user at CONFIRM so the next message
        # will be handled by _handle_edit_request via the dispatch above.
        # Actually we detect edit sub-commands inline next time.
        return

    # Check if the user is providing an inline edit (e.g., "change amount to 1000")
    edit_applied = await _try_inline_edit(user, lower, chat_id)
    if edit_applied:
        # Re-show the updated profile summary
        await show_profile_summary(user, chat_id)
        return

    # Unrecognised response -- re-prompt
    await send_message(
        chat_id,
        "Please reply YES to confirm your profile, or tell me what you'd "
        "like to change.",
    )


async def _try_inline_edit(
    user: User,
    text: str,
    chat_id: str,
) -> bool:
    """Attempt to parse an inline edit command at the CONFIRM step.

    Handles patterns like:
      - "change language to es"
      - "change sender country to UK"
      - "change amount to 1000"
      - "change level to advanced"

    Returns True if an edit was successfully applied.
    """
    # Mapping of keywords to onboarding steps for re-application
    edit_patterns: list[tuple[str, OnboardingStep]] = [
        ("language", OnboardingStep.LANGUAGE),
        ("sender", OnboardingStep.SENDER_COUNTRY),
        ("recipient", OnboardingStep.RECIPIENT_COUNTRY),
        ("amount", OnboardingStep.AMOUNT),
        ("level", OnboardingStep.LITERACY),
        ("literacy", OnboardingStep.LITERACY),
    ]

    for keyword, step in edit_patterns:
        # Match "change <keyword> to <value>" or "<keyword> <value>"
        pattern = rf"(?:change|set|update)?\s*{keyword}\s+(?:to\s+)?(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_value = match.group(1).strip()
            # Re-parse through the standard extraction pipeline
            extracted = await _extract_answer(step, raw_value)
            if extracted is not None:
                try:
                    await _apply_answer(user, step, extracted)
                    return True
                except ValueError as exc:
                    await send_message(chat_id, f"Could not apply that change: {exc}")
                    return True  # We handled the intent even though it failed

    return False


async def _complete_onboarding(user: User, chat_id: str) -> None:
    """Mark onboarding as complete and notify the user.

    Sets the user's ``onboarding_step`` to COMPLETE and sends a
    confirmation message indicating that rate monitoring has begun.
    """
    user.onboarding_step = OnboardingStep.COMPLETE
    await update_user(user)

    profile = await get_profile_by_user(user.user_id)
    corridor_display = profile.corridor if profile and profile.corridor else "your corridor"

    completion_msg = (
        "You're all set! I'm now monitoring exchange rates for "
        f"{corridor_display}.\n\n"
        "I'll notify you when conditions are favorable to send money. "
        "You can also update your preferences anytime by saying things like "
        "\"set threshold to 2%\" or \"change level to advanced\"."
    )

    await send_message(chat_id, completion_msg)

    logger.info(
        "Onboarding complete for user_id=%s, corridor=%s",
        user.user_id,
        corridor_display,
    )


async def _generate_question(step: OnboardingStep) -> str:
    """Generate the onboarding question for the given step.

    Tries the LLM first for a more natural, conversational tone.
    Falls back to the static template if the LLM is unavailable.
    """
    fallback = FallbackTemplates.onboarding_question(step)

    try:
        prompt = (
            f"Generate a short, friendly onboarding question for a remittance "
            f"service. The current step is: {step.value}.\n\n"
            f"Here is the default question for reference (rephrase naturally):\n"
            f"{fallback}"
        )
        llm_response = await _llm.invoke(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=256,
        )
        if llm_response and len(llm_response.strip()) > 10:
            return llm_response.strip()
    except Exception:
        logger.debug("LLM question generation failed for step=%s; using fallback", step.value)

    return fallback
