"""Wise sandbox API adapter — OAuth flow and transfer operations.

Covers Task 4.1 (OAuth) and Task 4.2 (API wrapper).  All HTTP calls
use ``httpx`` with a 10-second timeout.
"""

import logging
import urllib.parse

import httpx

from app.config import settings
from app.db.dynamodb import get_table

logger = logging.getLogger(__name__)

_TIMEOUT = 10  # seconds


# ──── Internal helpers ────


def _wise_headers(access_token: str) -> dict:
    """Return standard authorization headers for Wise API calls."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


# ──── Task 4.1 — Wise OAuth ────


def get_oauth_url(user_id: str) -> str:
    """Build the Wise OAuth authorization URL.

    The *user_id* is passed as the ``state`` parameter so the callback
    can associate the code with the correct user.
    """
    params = {
        "client_id": settings.wise_client_id,
        "redirect_uri": settings.wise_redirect_uri,
        "state": user_id,
    }
    return (
        f"{settings.wise_api_base_url}/oauth/authorize?"
        f"{urllib.parse.urlencode(params)}"
    )


async def exchange_oauth_code(code: str, state: str) -> dict | None:
    """Exchange an OAuth authorization *code* for an access/refresh token pair.

    *state* is the ``user_id`` that was embedded in the authorization URL.
    On success the tokens are persisted in the ``wise_tokens`` DynamoDB
    table and the full token payload is returned.  Returns ``None`` on
    any failure.
    """
    url = f"{settings.wise_api_base_url}/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.wise_client_id,
        "client_secret": settings.wise_client_secret,
        "code": code,
        "redirect_uri": settings.wise_redirect_uri,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            token_data = resp.json()

        # Persist tokens
        table = get_table("wise_tokens")
        table.put_item(
            Item={
                "user_id": state,
                "access_token": token_data.get("access_token", ""),
                "refresh_token": token_data.get("refresh_token", ""),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": str(token_data.get("expires_in", 0)),
            }
        )
        logger.info("Stored Wise OAuth tokens for user=%s", state)
        return token_data

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Wise OAuth token exchange HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Wise OAuth token exchange request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error during Wise OAuth token exchange")
    return None


async def refresh_token(user_id: str) -> str | None:
    """Refresh the Wise access token for *user_id*.

    Reads the stored refresh token from DynamoDB, calls the Wise token
    endpoint, persists the new tokens, and returns the new access token.
    Returns ``None`` on any failure.
    """
    table = get_table("wise_tokens")
    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    if not item or not item.get("refresh_token"):
        logger.warning("No refresh token found for user=%s", user_id)
        return None

    url = f"{settings.wise_api_base_url}/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": settings.wise_client_id,
        "client_secret": settings.wise_client_secret,
        "refresh_token": item["refresh_token"],
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            http_resp = await client.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            http_resp.raise_for_status()
            token_data = http_resp.json()

        # Persist updated tokens
        table.put_item(
            Item={
                "user_id": user_id,
                "access_token": token_data.get("access_token", ""),
                "refresh_token": token_data.get("refresh_token", ""),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": str(token_data.get("expires_in", 0)),
            }
        )
        logger.info("Refreshed Wise access token for user=%s", user_id)
        return token_data.get("access_token")

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Wise token refresh HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Wise token refresh request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error during Wise token refresh")
    return None


# ──── Task 4.2 — Wise API wrapper ────


async def create_quote(
    access_token: str,
    source_currency: str,
    target_currency: str,
    amount: float,
) -> dict | None:
    """Create a Wise quote via ``POST /v3/quotes``.

    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    url = f"{settings.wise_api_base_url}/v3/quotes"
    payload = {
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "sourceAmount": amount,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                json=payload,
                headers=_wise_headers(access_token),
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info(
            "Created Wise quote %s (%s -> %s, amount=%.2f)",
            data.get("id"),
            source_currency,
            target_currency,
            amount,
        )
        return data

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Wise create_quote HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Wise create_quote request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error creating Wise quote")
    return None


async def create_transfer(
    access_token: str,
    quote_id: str,
    target_account: str,
) -> dict | None:
    """Create a Wise transfer via ``POST /v1/transfers``.

    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    url = f"{settings.wise_api_base_url}/v1/transfers"
    payload = {
        "targetAccount": target_account,
        "quoteUuid": quote_id,
        "customerTransactionId": None,  # Wise generates one
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                json=payload,
                headers=_wise_headers(access_token),
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info(
            "Created Wise transfer %s (quote=%s, target_account=%s)",
            data.get("id"),
            quote_id,
            target_account,
        )
        return data

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Wise create_transfer HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Wise create_transfer request failed: %s", exc)
    except Exception:
        logger.exception("Unexpected error creating Wise transfer")
    return None


async def get_transfer_status(
    access_token: str,
    transfer_id: str,
) -> dict | None:
    """Retrieve transfer status via ``GET /v1/transfers/{id}``.

    Returns the parsed JSON response on success, or ``None`` on failure.
    """
    url = f"{settings.wise_api_base_url}/v1/transfers/{transfer_id}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                url,
                headers=_wise_headers(access_token),
            )
            resp.raise_for_status()
            data = resp.json()

        logger.debug(
            "Wise transfer %s status: %s",
            transfer_id,
            data.get("status"),
        )
        return data

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Wise get_transfer_status HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Wise get_transfer_status request failed: %s", exc)
    except Exception:
        logger.exception(
            "Unexpected error fetching Wise transfer status for %s",
            transfer_id,
        )
    return None
