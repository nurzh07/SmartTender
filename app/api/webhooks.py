"""
WebHook handlers:
  POST /webhooks/goszakupki  – Goszakupki.kz updates
  POST /webhooks/telegram    – Telegram bot updates (via webhook mode)
  POST /webhooks/stripe      – Stripe payment events
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.tender import Tender, TenderStatus
from app.tasks.goszakupki_tasks import import_open_tenders_from_goszakupki

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# GOSZAKUPKI.KZ webhook
# ──────────────────────────────────────────────────────────────

@router.post("/goszakupki", tags=["webhooks"])
async def goszakupki_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive external updates from goszakupki.kz."""
    payload = await request.json()
    event = payload.get("event", "tender.updated")
    data = payload.get("data", {})

    if event == "tender.updated" and data.get("external_id"):
        tender = db.query(Tender).filter(Tender.external_id == data["external_id"]).first()
        if tender:
            if data.get("title"):
                tender.title = data["title"]
            if data.get("status") == "closed":
                tender.status = TenderStatus.CLOSED
            db.commit()
            return {"status": "updated", "tender_id": tender.id}

    if event == "import.request":
        task = import_open_tenders_from_goszakupki.delay(limit=data.get("limit", 10))
        return {"status": "import_queued", "task_id": task.id}

    return {"status": "ignored", "event": event}


# ──────────────────────────────────────────────────────────────
# TELEGRAM webhook (webhook mode for production)
# ──────────────────────────────────────────────────────────────

@router.post("/telegram", tags=["webhooks"])
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    """
    Receive Telegram bot updates via webhook.
    Validates the X-Telegram-Bot-Api-Secret-Token header if TELEGRAM_WEBHOOK_SECRET is set.
    """
    # Optional secret validation
    if (
        settings.TELEGRAM_WEBHOOK_SECRET
        and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        from telegram import Update
        from app.telegram.bot import create_bot_application

        bot_app = create_bot_application()
        if bot_app is None:
            return {"ok": True, "status": "bot_disabled"}

        # Initialize bot if not already done
        if not bot_app._initialized:  # noqa: SLF001
            await bot_app.initialize()

        update = Update.de_json(body, bot_app.bot)
        await bot_app.process_update(update)
        return {"ok": True}
    except Exception as exc:
        logger.error("Telegram webhook processing error: %s", exc)
        # Return 200 even on error so Telegram doesn't retry
        return {"ok": True, "error": str(exc)}


# ──────────────────────────────────────────────────────────────
# STRIPE webhook
# ──────────────────────────────────────────────────────────────

@router.post("/stripe", tags=["webhooks"])
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """
    Receive Stripe webhook events.

    Handles:
      - payment_intent.succeeded   → publish tender, mark deposit paid
      - payment_intent.payment_failed → notify buyer, keep tender as DRAFT
      - charge.refunded             → mark deposit as returned
    """
    payload_bytes = await request.body()

    # Verify Stripe signature
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if settings.STRIPE_WEBHOOK_SECRET and stripe_signature:
            event = stripe.Webhook.construct_event(
                payload_bytes, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # In development without signature verification
            import json
            event = stripe.Event.construct_from(
                json.loads(payload_bytes), stripe.api_key
            )
    except Exception as exc:
        logger.error("Stripe webhook signature error: %s", exc)
        raise HTTPException(status_code=400, detail=f"Webhook error: {exc}")

    # Handle events
    try:
        from app.services.stripe_service import (
            handle_payment_succeeded,
            handle_payment_failed,
            handle_charge_refunded,
        )

        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            handle_payment_succeeded(db, event_data["id"])
            logger.info("Stripe: payment succeeded — %s", event_data["id"])

        elif event_type == "payment_intent.payment_failed":
            handle_payment_failed(db, event_data["id"])
            logger.info("Stripe: payment failed — %s", event_data["id"])

        elif event_type == "charge.refunded":
            handle_charge_refunded(db, event_data.get("payment_intent"))
            logger.info("Stripe: charge refunded — %s", event_data.get("payment_intent"))

        else:
            logger.debug("Stripe: unhandled event type %s", event_type)

    except Exception as exc:
        logger.error("Error handling Stripe event %s: %s", event.get("type"), exc)
        # Return 200 to acknowledge receipt; log error internally
        return {"received": True, "error": str(exc)}

    return {"received": True, "type": event.get("type")}
