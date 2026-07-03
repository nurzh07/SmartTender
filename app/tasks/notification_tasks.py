"""
Celery notification tasks — Email + Telegram.
"""

import logging

import httpx

from app.config import get_settings
from app.tasks.celery_app import celery_app
from app.tasks.email_tasks import send_email_notification

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# LOW-LEVEL TELEGRAM SENDER
# ═══════════════════════════════════════════════════════════════

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_telegram_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
    """Send a single Telegram message. Retried up to 3 times on failure."""
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.info("Telegram skipped (no token/chat_id): %s", text[:80])
        return {"status": "skipped"}
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode})
            r.raise_for_status()
        return {"status": "sent", "chat_id": chat_id}
    except Exception as exc:
        logger.warning("Telegram error (%s): %s", chat_id, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"status": "error", "detail": str(exc)}


# ═══════════════════════════════════════════════════════════════
# TENDER PUBLISHED — notify ALL suppliers
# ═══════════════════════════════════════════════════════════════

@celery_app.task
def notify_tender_published(tender_id: int, title: str, budget: float, emails: list[str]) -> dict:
    """Notify suppliers about new published tender via email + Telegram."""
    app_url = settings.APP_PUBLIC_URL.rstrip("/")
    subject = f"Жаңа тендер: {title}"
    email_body = (
        f"Тендер #{tender_id} «{title}» жарияланды.\n"
        f"Ұсыныс жіберу: {app_url}/tenders/{tender_id}"
    )
    # Email
    for email in emails:
        send_email_notification.delay(email, subject, email_body)

    # Telegram — fan-out to all suppliers with linked accounts
    from app.telegram.notifications import notify_new_tender_sync
    sent = notify_new_tender_sync(tender_id, title, budget)
    return {"status": "queued", "email_recipients": len(emails), "telegram_sent": sent}


# ═══════════════════════════════════════════════════════════════
# NEW PROPOSAL — notify BUYER
# ═══════════════════════════════════════════════════════════════

@celery_app.task
def notify_proposal_received(
    buyer_email: str, buyer_chat_id: str | None,
    tender_title: str, supplier_name: str, price: float,
) -> dict:
    """Notify buyer about a new proposal via email + Telegram."""
    subject = f"Жаңа ұсыныс: {tender_title}"
    message = (
        f"«{tender_title}» тендеріне {supplier_name} жаңа ұсыныс жіберді.\n"
        f"Баға: {price:,.0f} ₸"
    )
    send_email_notification.delay(buyer_email, subject, message)

    if buyer_chat_id:
        from app.telegram.notifications import notify_new_proposal_sync
        notify_new_proposal_sync(buyer_chat_id, tender_title, supplier_name, price)

    return {"status": "queued", "buyer_email": buyer_email, "telegram": bool(buyer_chat_id)}


# ═══════════════════════════════════════════════════════════════
# APPROVAL RESULT — notify TENDER CREATOR
# ═══════════════════════════════════════════════════════════════

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
        chat_id = user.telegram_chat_id if user else None
    finally:
        db.close()

    send_email_notification.delay(email=email, subject=f"Бекіту: {status_text}", message=message)
    if chat_id:
        emoji = "✅" if approved else "❌"
        send_telegram_message.delay(chat_id, f"{emoji} {message}")
    return {"status": "queued", "user_id": user_id}


# ═══════════════════════════════════════════════════════════════
# DEADLINE REMINDER (–3 days) — notify ALL participants
# ═══════════════════════════════════════════════════════════════

@celery_app.task
def notify_deadline_reminder(tender_id: int, title: str, days_left: int, emails: list[str]) -> dict:
    """Notify participants of upcoming deadline via email + Telegram."""
    subject = f"Дедлайн {days_left} күн: {title}"
    email_body = f"Тендер #{tender_id} «{title}» аяқталуына {days_left} күн қалды."
    for email in emails:
        send_email_notification.delay(email, subject, email_body)

    # Telegram — all participants with linked accounts for this tender
    from app.database import SessionLocal
    from app.models.proposal import TenderProposal
    from app.models.tender import Tender
    from app.models.user import User
    from app.telegram.notifications import notify_deadline_reminder_sync

    db = SessionLocal()
    try:
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        chat_ids: list[str] = []

        # buyer
        if tender:
            buyer = db.query(User).filter(User.id == tender.created_by).first()
            if buyer and buyer.telegram_chat_id:
                chat_ids.append(buyer.telegram_chat_id)

        # suppliers with proposals
        proposals = db.query(TenderProposal).filter(TenderProposal.tender_id == tender_id).all()
        for p in proposals:
            supplier = db.query(User).filter(User.id == p.supplier_id).first()
            if supplier and supplier.telegram_chat_id and supplier.telegram_chat_id not in chat_ids:
                chat_ids.append(supplier.telegram_chat_id)

        sent = notify_deadline_reminder_sync(chat_ids, title, tender_id, days_left)
    finally:
        db.close()

    return {"status": "queued", "days_left": days_left, "telegram_sent": sent}


# ═══════════════════════════════════════════════════════════════
# WINNER SELECTED — notify winner + losers
# ═══════════════════════════════════════════════════════════════

@celery_app.task
def notify_tender_awarded(
    tender_id: int, title: str, winner_email: str, loser_emails: list[str]
) -> dict:
    """Notify winner and losers via email + Telegram."""
    send_email_notification.delay(
        winner_email,
        f"🎉 Тендер #{tender_id} — Жеңімпаз!",
        f"Сіз «{title}» тендерінде жеңімпаз атандыңыз! Құттықтаймыз!",
    )
    for email in loser_emails:
        send_email_notification.delay(
            email,
            f"Тендер #{tender_id} нәтижесі",
            f"«{title}» тендерінде таңдау басқа ұсынысқа түсті. Қатысқаныңыз үшін рахмет.",
        )

    # Telegram
    from app.database import SessionLocal
    from app.models.proposal import TenderProposal
    from app.models.user import User
    from app.telegram.notifications import notify_winner_sync

    db = SessionLocal()
    try:
        proposals = (
            db.query(TenderProposal)
            .filter(TenderProposal.tender_id == tender_id)
            .order_by(TenderProposal.score.desc())
            .all()
        )
        winner_chat_id = None
        loser_chat_ids = []
        for i, p in enumerate(proposals):
            supplier = db.query(User).filter(User.id == p.supplier_id).first()
            if not supplier or not supplier.telegram_chat_id:
                continue
            if i == 0:
                winner_chat_id = supplier.telegram_chat_id
            else:
                loser_chat_ids.append(supplier.telegram_chat_id)

        if winner_chat_id:
            notify_winner_sync(winner_chat_id, loser_chat_ids, title, tender_id)
    finally:
        db.close()

    return {"status": "queued", "winner": winner_email, "losers": len(loser_emails)}


# ═══════════════════════════════════════════════════════════════
# TENDER CLOSED — notify buyer
# ═══════════════════════════════════════════════════════════════

@celery_app.task
def notify_tender_closed(buyer_email: str, tender_id: int, title: str, report_url: str) -> dict:
    subject = f"Тендер жабылды: {title}"
    message = (
        f"«{title}» (#{tender_id}) тендері жабылды.\n"
        f"Есеп: {settings.APP_PUBLIC_URL}{report_url}"
    )
    send_email_notification.delay(buyer_email, subject, message)
    return {"status": "queued", "buyer_email": buyer_email}
