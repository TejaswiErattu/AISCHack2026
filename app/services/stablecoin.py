"""CoinGecko integration for stablecoin prices and route simulation."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Stablecoin IDs understood by CoinGecko
_COINGECKO_IDS = "usd-coin,tether"

# Fiat currencies we care about for stablecoin off-ramp quotes
_VS_CURRENCIES = "usd,inr,php,mxn,gbp"

# Fee assumptions for stablecoin route simulation
_ON_RAMP_FEE_PCT = 0.1   # USD -> USDC (on-ramp)
_OFF_RAMP_FEE_PCT = 0.5  # USDC -> target fiat (off-ramp)


# ──── Task 2.2 — CoinGecko client ────


async def fetch_stablecoin_prices() -> dict | None:
    """Fetch USDC and USDT prices in several fiat currencies from CoinGecko.

    Returns a dict keyed by stablecoin ticker (``usdc``, ``usdt``), each
    mapping to a dict of ``{currency: price}``.  Example::

        {
            "usdc": {"usd": 1.0, "inr": 83.2, ...},
            "usdt": {"usd": 1.0, "inr": 83.1, ...},
        }

    Returns ``None`` on any error.
    """
    url = (
        f"{settings.coingecko_api_base_url}/simple/price"
        f"?ids={_COINGECKO_IDS}&vs_currencies={_VS_CURRENCIES}"
    )
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        # Map CoinGecko IDs to short tickers
        result: dict[str, dict[str, float]] = {}

        usdc_data = data.get("usd-coin")
        if usdc_data:
            result["usdc"] = {k: float(v) for k, v in usdc_data.items()}

        usdt_data = data.get("tether")
        if usdt_data:
            result["usdt"] = {k: float(v) for k, v in usdt_data.items()}

        if not result:
            logger.warning("CoinGecko response contained no recognised stablecoin data")
            return None

        logger.debug("Fetched stablecoin prices: %s", result)
        return result

    except httpx.HTTPStatusError as exc:
        logger.error(
            "CoinGecko HTTP error %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("CoinGecko request failed: %s", exc)
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("CoinGecko unexpected payload: %s", exc)
    return None


# ──── Task 3.3 — Stablecoin route comparison ────


async def compute_stablecoin_route(
    amount_sent: float,
    target_currency: str,
) -> dict | None:
    """Estimate the payout for a USD -> USDC -> target fiat stablecoin route.

    The simulation applies:
      * An on-ramp fee (USD -> USDC): ``_ON_RAMP_FEE_PCT`` %
      * An off-ramp fee (USDC -> target fiat): ``_OFF_RAMP_FEE_PCT`` %

    Returns a dict with ``stablecoin_recipient_amount``, ``total_fees_pct``,
    ``stablecoin``, and ``route``, or ``None`` if prices are unavailable or the
    target currency is not supported.
    """
    prices = await fetch_stablecoin_prices()
    if prices is None:
        logger.warning("Cannot compute stablecoin route — price fetch failed")
        return None

    usdc_prices = prices.get("usdc")
    if usdc_prices is None:
        logger.warning("USDC price data unavailable")
        return None

    target_key = target_currency.lower()
    target_rate = usdc_prices.get(target_key)
    if target_rate is None:
        logger.warning(
            "No USDC/%s rate available from CoinGecko (have: %s)",
            target_currency,
            list(usdc_prices.keys()),
        )
        return None

    # Step 1: USD -> USDC (apply on-ramp fee)
    usdc_amount = amount_sent * (1 - _ON_RAMP_FEE_PCT / 100)

    # Step 2: USDC -> target fiat at CoinGecko rate (apply off-ramp fee)
    fiat_before_fee = usdc_amount * target_rate
    recipient_amount = fiat_before_fee * (1 - _OFF_RAMP_FEE_PCT / 100)

    total_fees_pct = _ON_RAMP_FEE_PCT + _OFF_RAMP_FEE_PCT

    return {
        "stablecoin_recipient_amount": round(recipient_amount, 2),
        "total_fees_pct": total_fees_pct,
        "stablecoin": "USDC",
        "route": f"USD → USDC → {target_currency.upper()}",
    }
