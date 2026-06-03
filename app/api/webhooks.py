from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.tender import Tender, TenderStatus
from app.services.goszakupki_client import GoszakupkiClient
from app.tasks.goszakupki_tasks import import_open_tenders_from_goszakupki

router = APIRouter()
settings = get_settings()


@router.post("/goszakupki")
async def goszakupki_webhook(request: Request, db: Session = Depends(get_db)):
    """Сыртқы жаңартуларды қабылдау (goszakupki.kz)."""
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


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    if settings.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    payload = await request.json()
    message = payload.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    from app.tasks.notification_tasks import send_telegram_message

    if chat_id and text.startswith("/start"):
        send_telegram_message.delay(str(chat_id), "SmartTender бот қосылды!")

    return {"ok": True}
