import logging

import httpx

from app.config import get_settings
from app.tasks.celery_app import celery_app
from app.tasks.email_tasks import send_email_notification

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task
def send_telegram_message(chat_id: str, text: str) -> dict:
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.info("Telegram skipped (no token/chat): %s", text[:80])
        return {"status": "skipped"}
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(url, json={"chat_id": chat_id, "text": text})
            r.raise_for_status()
        return {"status": "sent"}
    except Exception as exc:
        logger.warning("Telegram error: %s", exc)
        return {"status": "error", "detail": str(exc)}


@celery_app.task
def notify_tender_published(tender_id: int, title: str, emails: list, user_ids: list) -> dict:
    subject = f"Жаңа тендер: {title}"
    message = f"Тендер #{tender_id} жарияланды. Ұсыныс жіберіңіз: {settings.APP_PUBLIC_URL}/docs"
    for email in emails:
        send_email_notification.delay(email, subject, message)
    return {"status": "queued", "recipients": len(emails)}


@celery_app.task
def notify_approval_result(user_id: int, approved: bool, tender_title: str) -> dict:
    from app.database import SessionLocal
    from app.models.user import User

    status_text = "бекітілді" if approved else "қабылданбады"
    message = f"Өтінім «{tender_title}» {status_text}."
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        email = user.email if user else f"user{user_id}@smarttender.local"
    finally:
        db.close()
    send_email_notification.delay(email=email, subject=f"Бекіту: {status_text}", message=message)
    return {"status": "queued", "user_id": user_id}


@celery_app.task
def notify_deadline_reminder(tender_id: int, title: str, days_left: int, emails: list) -> dict:
    subject = f"Дедлайн {days_left} күн: {title}"
    message = f"Тендер #{tender_id} аяқталуына {days_left} күн қалды."
    for email in emails:
        send_email_notification.delay(email, subject, message)
    return {"status": "queued", "days_left": days_left}


@celery_app.task
def notify_tender_awarded(
    tender_id: int, title: str, winner_name: str, user_ids: list
) -> dict:
    message = f"Тендер «{title}» жеңімпазы: {winner_name}"
    send_email_notification.delay(
        email="participants@smarttender.local",
        subject=f"Нәтиже тендер #{tender_id}",
        message=message,
    )
    return {"status": "queued"}
