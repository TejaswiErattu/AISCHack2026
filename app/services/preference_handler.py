"""Preference update handler for RemitAgent.

Parses natural-language preference update requests and persists validated
changes to the user's ``UserPreferences`` record in DynamoDB.

Supported preferences:
  - financial_literacy_level: beginner / intermediate / advanced
  - alert_threshold_pct: 0.1 -- 10.0 (percentage)
  - language: ISO 639-1 code
  - payout_method: bank_transfer / mobile_wallet / cash_pickup

Uses LLM structured extraction first, falling back to simple regex parsing
for common patterns.
"""

import json
import logging
import re

from app.db.crud import (
    get_preferences,
    get_profile_by_user,
    update_preferences,
    update_profile,
    update_user,
)
from app.llm.bedrock import BedrockClient
from app.llm.prompts import PREFERENCE_UPDATE_PROMPT, SYSTEM_PROMPT
from app.models.schemas import LiteracyLevel, User
from app.services.telegram import send_message

logger = logging.getLogger(__name__)

# ──── Constants ────

_VALID_LITERACY_LEVELS = {level.value for level in LiteracyLevel}

_VALID_PAYOUT_METHODS = {"bank_transfer", "mobile_wallet", "cash_pickup"}

_THRESHOLD_MIN = 0.1
_THRESHOLD_MAX = 10.0

# Shared LLM client instance.
_llm = BedrockClient()


# ──── Public API ────


async def handle_preference_update(
    user: User,
    message_text: str,
    chat_id: str,
) -> None:
    """Parse and apply a preference update from the user's message.

    Attempts LLM-based structured extraction first.  If the LLM is
    unavailable or returns nothing useful, falls back to regex-based
    parsing for common patterns.

    Validates every value before persisting and sends a confirmation
    (or error) message to the user via Telegram.

    Args:
        user: The authenticated ``User`` model.
        message_text: Raw text from the user's Telegram message.
        chat_id: Telegram chat ID for sending replies.
    """
    logger.info(
        "Processing preference update for user_id=%s: %s",
        user.user_id,
        message_text[:120],
    )

    updates = await _extract_updates(message_text)

    if not updates:
        await send_message(
            chat_id,
            "I couldn't understand that preference update. You can say things like:\n\n"
            "- \"set threshold to 2%\"\n"
            "- \"change level to advanced\"\n"
            "- \"set language to Spanish\"\n"
            "- \"change payout to mobile wallet\"",
        )
        return

    # Apply each update individually so partial success is possible.
    applied: list[str] = []
    errors: list[str] = []

    for field, value in updates:
        try:
            description = await _apply_update(user, field, value)
            applied.append(description)
        except ValueError as exc:
            errors.append(str(exc))

    # Build response message
    response_parts: list[str] = []
    if applied:
        response_parts.append("Updated:\n" + "\n".join(f"  - {d}" for d in applied))
    if errors:
        response_parts.append("Could not apply:\n" + "\n".join(f"  - {e}" for e in errors))

    await send_message(chat_id, "\n\n".join(response_parts))

    logger.info(
        "Preference update for user_id=%s: %d applied, %d errors",
        user.user_id,
        len(applied),
        len(errors),
    )


# ──── Extraction ────


async def _extract_updates(message_text: str) -> list[tuple[str, str | float]]:
    """Extract preference field/value pairs from the user's message.

    Tries the LLM first, then falls back to regex parsing.

    Returns a list of ``(field_name, value)`` tuples.
    """
    # ── LLM extraction ──
    updates = await _extract_via_llm(message_text)
    if updates:
        return updates

    # ── Regex fallback ──
    return _extract_via_regex(message_text)


async def _extract_via_llm(message_text: str) -> list[tuple[str, str | float]]:
    """Use the LLM to parse preference updates from free text.

    Returns an empty list if the LLM is unavailable or the response
    cannot be parsed.
    """
    try:
        raw = await _llm.extract_structured(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"{PREFERENCE_UPDATE_PROMPT}\n\nUser's message: {message_text}"
            ),
        )
        if not raw:
            return []

        return _parse_llm_response(raw)

    except Exception:
        logger.exception("LLM preference extraction failed")
        return []


def _parse_llm_response(raw: str) -> list[tuple[str, str | float]]:
    """Parse the LLM's JSON response into a list of (field, value) tuples."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("LLM returned non-JSON for preference update: %s", raw[:200])
        return []

    raw_updates = data.get("updates", [])
    if not isinstance(raw_updates, list):
        return []

    results: list[tuple[str, str | float]] = []
    for item in raw_updates:
        field = item.get("field")
        value = item.get("value")
        if field and value is not None:
            results.append((str(field), value))

    return results


def _extract_via_regex(message_text: str) -> list[tuple[str, str | float]]:
    """Regex-based fallback parser for common preference update patterns.

    Handles patterns like:
      - "set threshold to 2%"
      - "change level to advanced"
      - "set language to es" / "set language to Spanish"
      - "change payout to mobile wallet"
    """
    text = message_text.strip().lower()
    results: list[tuple[str, str | float]] = []

    # ── Threshold ──
    threshold_match = re.search(
        r"(?:threshold|alert)\s+(?:to\s+)?(\d+(?:\.\d+)?)\s*%?",
        text,
    )
    if threshold_match:
        results.append(("alert_threshold_pct", float(threshold_match.group(1))))

    # ── Literacy level ──
    level_match = re.search(
        r"(?:level|literacy)\s+(?:to\s+)?(beginner|intermediate|advanced)",
        text,
    )
    if level_match:
        results.append(("financial_literacy_level", level_match.group(1)))

    # ── Language ──
    lang_match = re.search(
        r"(?:language)\s+(?:to\s+)?(\w+)",
        text,
    )
    if lang_match:
        lang_value = _normalize_language(lang_match.group(1))
        if lang_value:
            results.append(("language", lang_value))

    # ── Payout method ──
    payout_match = re.search(
        r"(?:payout|payment)\s+(?:method\s+)?(?:to\s+)?"
        r"(bank.?transfer|mobile.?wallet|cash.?pickup)",
        text,
    )
    if payout_match:
        method = re.sub(r"[\s\-]", "_", payout_match.group(1).strip())
        results.append(("payout_method", method))

    return results


def _normalize_language(text: str) -> str | None:
    """Convert a language name or code to an ISO 639-1 code."""
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
    if len(lower) == 2 and lower.isalpha():
        return lower
    return mapping.get(lower)


# ──── Validation & Application ────


async def _apply_update(
    user: User,
    field: str,
    value: str | float,
) -> str:
    """Validate and persist a single preference update.

    Returns a human-readable description of what was changed.
    Raises ``ValueError`` if the value is invalid.
    """
    if field == "alert_threshold_pct":
        return await _apply_threshold(user, value)

    if field == "financial_literacy_level":
        return await _apply_literacy_level(user, value)

    if field == "language":
        return await _apply_language(user, value)

    if field == "payout_method":
        return await _apply_payout_method(user, value)

    raise ValueError(f"Unknown preference field: {field}")


async def _apply_threshold(user: User, value: str | float) -> str:
    """Validate and apply an alert threshold update."""
    try:
        threshold = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"'{value}' is not a valid number for the alert threshold."
        )

    if threshold < _THRESHOLD_MIN or threshold > _THRESHOLD_MAX:
        raise ValueError(
            f"Alert threshold must be between {_THRESHOLD_MIN}% and "
            f"{_THRESHOLD_MAX}%. You provided {threshold}%."
        )

    prefs = await get_preferences(user.user_id)
    if not prefs:
        raise ValueError("User preferences not found. Please complete onboarding first.")

    old_value = prefs.alert_threshold_pct
    prefs.alert_threshold_pct = threshold
    await update_preferences(prefs)

    logger.info(
        "Updated alert_threshold_pct for user_id=%s: %.1f%% -> %.1f%%",
        user.user_id,
        old_value,
        threshold,
    )
    return f"Alert threshold: {old_value}% -> {threshold}%"


async def _apply_literacy_level(user: User, value: str | float) -> str:
    """Validate and apply a financial literacy level update."""
    level_str = str(value).lower().strip()

    if level_str not in _VALID_LITERACY_LEVELS:
        raise ValueError(
            f"'{value}' is not a valid literacy level. "
            f"Choose from: {', '.join(sorted(_VALID_LITERACY_LEVELS))}."
        )

    prefs = await get_preferences(user.user_id)
    if not prefs:
        raise ValueError("User preferences not found. Please complete onboarding first.")

    old_value = prefs.financial_literacy_level.value
    prefs.financial_literacy_level = LiteracyLevel(level_str)
    await update_preferences(prefs)

    logger.info(
        "Updated literacy level for user_id=%s: %s -> %s",
        user.user_id,
        old_value,
        level_str,
    )
    return f"Explanation level: {old_value.title()} -> {level_str.title()}"


async def _apply_language(user: User, value: str | float) -> str:
    """Validate and apply a language preference update."""
    lang_code = str(value).lower().strip()

    if len(lang_code) != 2 or not lang_code.isalpha():
        # Try normalizing from a language name
        normalized = _normalize_language(lang_code)
        if normalized is None:
            raise ValueError(
                f"'{value}' is not a recognized language. "
                "Please use a language name (e.g. Spanish) or "
                "ISO code (e.g. es)."
            )
        lang_code = normalized

    old_value = user.language
    user.language = lang_code
    await update_user(user)

    logger.info(
        "Updated language for user_id=%s: %s -> %s",
        user.user_id,
        old_value,
        lang_code,
    )
    return f"Language: {old_value} -> {lang_code}"


async def _apply_payout_method(user: User, value: str | float) -> str:
    """Validate and apply a payout method update."""
    method = str(value).lower().strip().replace(" ", "_").replace("-", "_")

    if method not in _VALID_PAYOUT_METHODS:
        raise ValueError(
            f"'{value}' is not a valid payout method. "
            f"Choose from: {', '.join(sorted(_VALID_PAYOUT_METHODS))}."
        )

    profile = await get_profile_by_user(user.user_id)
    if not profile:
        raise ValueError("Remittance profile not found. Please complete onboarding first.")

    old_value = profile.payout_method
    profile.payout_method = method
    await update_profile(profile)

    logger.info(
        "Updated payout_method for user_id=%s: %s -> %s",
        user.user_id,
        old_value,
        method,
    )
    display_name = method.replace("_", " ").title()
    old_display = old_value.replace("_", " ").title()
    return f"Payout method: {old_display} -> {display_name}"
