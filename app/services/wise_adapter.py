"""Wise sandbox API adapter — personal token auth and transfer operations.

Uses a personal API token from the Wise sandbox settings page.
All HTTP calls use ``httpx`` with a 10-second timeout.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 10  # seconds


def _wise_headers() -> dict:
    """Return authorization headers using the personal API token."""
    return {
        "Authorization": f"Bearer {settings.wise_api_token}",
        "Content-Type": "application/json",
    }


def is_configured() -> bool:
    """Check whether Wise credentials are available."""
    return bool(settings.wise_api_token)


# ──── Profile ────


async def get_profile_id() -> int | None:
    """Fetch the Wise personal profile ID (needed for quotes).

    Returns the first personal profile ID, or None on failure.
    """
    url = f"{settings.wise_api_base_url}/v2/profiles"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_wise_headers())
            resp.raise_for_status()
            profiles = resp.json()

        for p in profiles:
            if p.get("type") == "PERSONAL":
                return p["id"]

        logger.warning("No personal profile found in Wise response")
    except httpx.HTTPStatusError as exc:
        logger.error("Wise get_profile HTTP error %s: %s", exc.response.status_code, exc.response.text)
    except httpx.RequestError as exc:
        logger.error("Wise get_profile request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error fetching Wise profile")
    return None


# ──── Quotes ────


async def create_quote(
    source_currency: str,
    target_currency: str,
    amount: float,
    profile_id: int | None = None,
) -> dict | None:
    """Create a Wise quote via ``POST /v3/quotes``.

    If *profile_id* is not provided, it will be fetched automatically.
    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    if profile_id is None:
        profile_id = await get_profile_id()
        if profile_id is None:
            logger.error("Cannot create quote — no Wise profile ID")
            return None

    url = f"{settings.wise_api_base_url}/v3/profiles/{profile_id}/quotes"
    payload = {
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "sourceAmount": amount,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=_wise_headers())
            resp.raise_for_status()
            data = resp.json()

        logger.info(
            "Created Wise quote %s (%s -> %s, amount=%.2f)",
            data.get("id"), source_currency, target_currency, amount,
        )
        return data
    except httpx.HTTPStatusError as exc:
        logger.error("Wise create_quote HTTP error %s: %s", exc.response.status_code, exc.response.text)
    except httpx.RequestError as exc:
        logger.error("Wise create_quote request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error creating Wise quote")
    return None


# ──── Transfers ────


async def create_transfer(
    quote_id: str,
    target_account: int,
    profile_id: int | None = None,
) -> dict | None:
    """Create a Wise transfer via ``POST /v1/transfers``.

    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    if profile_id is None:
        profile_id = await get_profile_id()
        if profile_id is None:
            logger.error("Cannot create transfer — no Wise profile ID")
            return None

    url = f"{settings.wise_api_base_url}/v1/transfers"
    payload = {
        "targetAccount": target_account,
        "quoteUuid": quote_id,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=_wise_headers())
            resp.raise_for_status()
            data = resp.json()

        logger.info(
            "Created Wise transfer %s (quote=%s)", data.get("id"), quote_id,
        )
        return data
    except httpx.HTTPStatusError as exc:
        logger.error("Wise create_transfer HTTP error %s: %s", exc.response.status_code, exc.response.text)
    except httpx.RequestError as exc:
        logger.error("Wise create_transfer request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error creating Wise transfer")
    return None


async def get_transfer_status(transfer_id: str) -> dict | None:
    """Retrieve transfer status via ``GET /v1/transfers/{id}``.

    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    url = f"{settings.wise_api_base_url}/v1/transfers/{transfer_id}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_wise_headers())
            resp.raise_for_status()
            data = resp.json()

        logger.debug("Wise transfer %s status: %s", transfer_id, data.get("status"))
        return data
    except httpx.HTTPStatusError as exc:
        logger.error("Wise get_transfer_status HTTP error %s: %s", exc.response.status_code, exc.response.text)
    except httpx.RequestError as exc:
        logger.error("Wise get_transfer_status request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error fetching Wise transfer status for %s", transfer_id)
    return None


# ──── Kept for backward compat with main.py webhook route ────


async def exchange_oauth_code(code: str, state: str) -> dict:
    """No-op — OAuth flow replaced by personal token auth."""
    return {"error": "OAuth flow not used. Configure WISE_API_TOKEN instead."}
