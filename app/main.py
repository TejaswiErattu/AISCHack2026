import logging

from fastapi import FastAPI, Request
from mangum import Mangum

from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(title="RemitAgent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Telegram bot webhook endpoint — receives updates from Telegram."""
    body = await request.json()
    logger.info("Telegram update received: %s", body.get("update_id"))

    from app.services.telegram import handle_update

    await handle_update(body)
    return {"ok": True}


@app.get("/wise/callback")
async def wise_oauth_callback(code: str, state: str = ""):
    """Wise OAuth callback — exchanges authorization code for token."""
    from app.services.wise_adapter import exchange_oauth_code

    result = await exchange_oauth_code(code, state)
    return result


# Lambda handler
handler = Mangum(app, lifespan="off")
