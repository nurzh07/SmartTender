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
def notify_tender_published(tender_id: int, title: str, emails: list[str]) -> dict:
    subject = f"Жаңа тендер: {title}"
    message = (
        f"Тендер #{tender_id} «{title}» жарияланды.\n"
        f"Ұсыныс жіберу: {settings.APP_PUBLIC_URL}/tenders/{tender_id}"
    )
    for email in emails:
        send_email_notification.delay(email, subject, message)
    return {"status": "queued", "recipients": len(emails)}


@celery_app.task
def notify_proposal_received(
    buyer_email: str, tender_title: str, supplier_name: str, price: str
) -> dict:
    subject = f"Жаңа ұсыныс: {tender_title}"
    message = (
        f"«{tender_title}» тендеріне {supplier_name} жаңа ұсыныс жіберді.\n"
        f"Баға: {price} ₸"
    )
    send_email_notification.delay(buyer_email, subject, message)
    return {"status": "queued", "buyer_email": buyer_email}


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
def notify_deadline_reminder(tender_id: int, title: str, days_left: int, emails: list[str]) -> dict:
    subject = f"Дедлайн {days_left} күн: {title}"
    message = f"Тендер #{tender_id} «{title}» аяқталуына {days_left} күн қалды."
    for email in emails:
        send_email_notification.delay(email, subject, message)
    return {"status": "queued", "days_left": days_left}


@celery_app.task
def notify_tender_awarded(tender_id: int, title: str, winner_email: str, loser_emails: list[str]) -> dict:
    send_email_notification.delay(
        winner_email,
        f"Құттықтаймыз! Тендер #{tender_id}",
        f"«{title}» тендерінде жеңімпаз атандыңыз!",
    )
    for email in loser_emails:
        send_email_notification.delay(
            email,
            f"Тендер #{tender_id} нәтижесі",
            f"«{title}» тендерінде таңдау басқа ұсынысқа түсті. Қатысқаныңыз үшін рахмет.",
        )
    return {"status": "queued", "winner": winner_email, "losers": len(loser_emails)}


@celery_app.task
def notify_tender_closed(buyer_email: str, tender_id: int, title: str, report_url: str) -> dict:
    subject = f"Тендер жабылды: {title}"
    message = (
        f"«{title}» (#{tender_id}) тендері жабылды.\n"
        f"Есеп: {settings.APP_PUBLIC_URL}{report_url}"
    )
    send_email_notification.delay(buyer_email, subject, message)
    return {"status": "queued", "buyer_email": buyer_email}
