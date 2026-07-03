"""
Telegram notification helpers for SmartTender.

These are called from Celery tasks (sync context), so we use
httpx directly instead of the async python-telegram-bot client.
"""

import logging

import httpx

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────── low-level ──────────────────────────

def _send_message_sync(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message synchronously via Bot API (for Celery workers)."""
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            r.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Telegram send error to %s: %s", chat_id, exc)
        return False


def _get_all_supplier_chat_ids(db) -> list[str]:
    suppliers = (
        db.query(User)
        .filter(
            User.role == UserRole.SUPPLIER,
            User.is_active.is_(True),
            User.telegram_chat_id.isnot(None),
        )
        .all()
    )
    return [u.telegram_chat_id for u in suppliers if u.telegram_chat_id]


def _get_buyer_chat_id(db, tender_created_by: int) -> str | None:
    user = db.query(User).filter(User.id == tender_created_by).first()
    return user.telegram_chat_id if user else None


# ─────────────────────────── notification functions ─────────────

def notify_new_tender_sync(tender_id: int, tender_title: str, budget: float) -> int:
    """Notify ALL suppliers about a new published tender. Returns count sent."""
    db = SessionLocal()
    sent = 0
    try:
        chat_ids = _get_all_supplier_chat_ids(db)
        app_url = settings.APP_PUBLIC_URL.rstrip("/")
        text = (
            f"🆕 <b>Жаңа тендер жарияланды!</b>\n\n"
            f"📋 <b>{tender_title}</b>\n"
            f"🆔 ID: {tender_id}\n"
            f"💰 Бюджет: {budget:,.0f} ₸\n\n"
            f"🔗 <a href='{app_url}/tenders/{tender_id}'>Ұсыныс жіберу</a>"
        )
        for cid in chat_ids:
            if _send_message_sync(cid, text):
                sent += 1
        logger.info("Notified %d/%d suppliers about tender %d", sent, len(chat_ids), tender_id)
    finally:
        db.close()
    return sent


def notify_new_proposal_sync(buyer_chat_id: str, tender_title: str, supplier_name: str, price: float) -> bool:
    """Notify BUYER about a new proposal."""
    text = (
        f"📨 <b>Жаңа ұсыныс келді!</b>\n\n"
        f"📋 Тендер: <b>{tender_title}</b>\n"
        f"👤 Жеткізуші: {supplier_name}\n"
        f"💰 Баға: {price:,.0f} ₸\n\n"
        f"SmartTender платформасына кіріп қараңыз."
    )
    return _send_message_sync(buyer_chat_id, text)


def notify_deadline_reminder_sync(chat_ids: list[str], tender_title: str, tender_id: int, days_left: int) -> int:
    """Notify all participants about deadline reminder."""
    text = (
        f"⏰ <b>Дедлайн ескерту!</b>\n\n"
        f"📋 <b>{tender_title}</b>\n"
        f"🆔 ID: {tender_id}\n"
        f"⚠️ <b>{days_left} күн</b> қалды!\n\n"
        f"Уақытты өткізіп алмаңыз!"
    )
    sent = 0
    for cid in chat_ids:
        if _send_message_sync(cid, text):
            sent += 1
    return sent


def notify_winner_sync(winner_chat_id: str, loser_chat_ids: list[str], tender_title: str, tender_id: int) -> None:
    """Notify winner and losers about tender result."""
    winner_text = (
        f"🎉 <b>Құттықтаймыз! Сіз жеңдіңіз!</b>\n\n"
        f"📋 Тендер: <b>{tender_title}</b>\n"
        f"🆔 ID: {tender_id}\n\n"
        f"Келесі қадамдар туралы хабарласамыз."
    )
    _send_message_sync(winner_chat_id, winner_text)

    loser_text = (
        f"📋 <b>{tender_title}</b> тендерінің нәтижесі белгілі болды.\n\n"
        f"😔 Өкінішке орай, бұл жолы жеңіле алмадыңыз.\n"
        f"Басқа тендерлерге қатысыңыз!"
    )
    for cid in loser_chat_ids:
        _send_message_sync(cid, loser_text)


def get_buyer_chat_id_by_tender(tender_id: int) -> str | None:
    """Fetch buyer's telegram chat id by tender id."""
    db = SessionLocal()
    try:
        from app.models.tender import Tender
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            return None
        return _get_buyer_chat_id(db, tender.created_by)
    finally:
        db.close()
