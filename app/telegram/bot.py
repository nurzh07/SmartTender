"""
SmartTender Telegram Bot.

Commands:
  /start      – welcome + registration link
  /tenders    – last 5 published tenders
  /mytenders  – buyer's active tenders (linked account)
  /proposals  – supplier's submitted proposals (linked account)
  /status ID  – tender current status
  /connect CODE – link SmartTender account
  /help       – all commands

Inline buttons:
  approve_tender:{id}  – buyer approves tender from Telegram
  reject_tender:{id}   – buyer rejects tender from Telegram
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import get_settings
from app.database import SessionLocal
from app.models.proposal import TenderProposal
from app.models.tender import Tender, TenderStatus
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

APP_URL = settings.APP_PUBLIC_URL.rstrip("/")


# ─────────────────────────── helpers ────────────────────────────

def _get_db():
    """Get a fresh DB session; caller must close it."""
    return SessionLocal()


def _get_linked_user(db, chat_id: str) -> User | None:
    return db.query(User).filter(User.telegram_chat_id == chat_id).first()


# ─────────────────────────── /start ─────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message + registration link."""
    text = (
        "🎉 <b>SmartTender-ге қош келдіңіз!</b>\n\n"
        "Қазақстанға арналған корпоративтік тендер платформасы.\n\n"
        "📋 <b>Қол жетімді командалар:</b>\n"
        "  /tenders — Ашық тендерлер (соңғы 5)\n"
        "  /mytenders — Менің тендерлерім (BUYER)\n"
        "  /proposals — Менің ұсыныстарым (SUPPLIER)\n"
        "  /status &lt;id&gt; — Тендер статусы\n"
        "  /connect &lt;код&gt; — Аккаунтты байланыстыру\n"
        "  /help — Барлық командалар\n\n"
        f"🔗 <a href='{APP_URL}/register'>Тіркелу</a>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────────────── /help ──────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📋 <b>SmartTender Bot командалары:</b>\n\n"
        "/start — Бастау\n"
        "/tenders — Ашық тендерлер тізімі (соңғы 5)\n"
        "/mytenders — Менің тендерлерім (BUYER үшін)\n"
        "/proposals — Менің ұсыныстарым (SUPPLIER үшін)\n"
        "/status &lt;id&gt; — Тендер статусын көру\n"
        "/connect &lt;код&gt; — Telegram аккаунтын байланыстыру\n"
        "/help — Осы анықтама\n\n"
        "🔔 <b>Хабарландырулар:</b>\n"
        "  • Жаңа тендер жарияланғанда\n"
        "  • Ұсыныс келгенде\n"
        "  • Дедлайнға 3 күн қалғанда\n"
        "  • Жеңімпаз таңдалғанда"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────────────── /tenders ───────────────────────────

async def tenders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Last 5 published tenders."""
    db = _get_db()
    try:
        rows = (
            db.query(Tender)
            .filter(Tender.status == TenderStatus.PUBLISHED)
            .order_by(Tender.created_at.desc())
            .limit(5)
            .all()
        )
        if not rows:
            await update.message.reply_text("Қазір ашық тендер жоқ.")
            return

        lines = ["📋 <b>Ашық тендерлер (соңғы 5):</b>\n"]
        for t in rows:
            deadline_str = t.deadline.strftime("%Y-%m-%d") if t.deadline else "—"
            lines.append(
                f"🔹 <b>{t.title}</b>\n"
                f"   💰 {float(t.budget):,.0f} ₸ · 📅 {deadline_str}\n"
                f"   🆔 ID: {t.id} · <a href='{APP_URL}/tenders/{t.id}'>Қарау</a>"
            )
        await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error("Error in /tenders: %s", e)
        await update.message.reply_text("⚠️ Мәліметтерді жүктеу кезінде қате орын алды.")
    finally:
        db.close()


# ─────────────────────────── /mytenders ─────────────────────────

async def my_tenders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Buyer's active tenders."""
    chat_id = str(update.effective_chat.id)
    db = _get_db()
    try:
        user = _get_linked_user(db, chat_id)
        if not user:
            await update.message.reply_text(
                "⚠️ Аккаунтыңыз байланыстырылмаған.\n"
                "Профильден код алып, <code>/connect КОД</code> деп жіберіңіз.",
                parse_mode="HTML",
            )
            return

        if user.role.value not in ("buyer", "superadmin"):
            await update.message.reply_text("ℹ️ Бұл команда тек BUYER рөлі үшін.")
            return

        rows = (
            db.query(Tender)
            .filter(
                Tender.created_by == user.id,
                Tender.status.in_([
                    TenderStatus.PUBLISHED,
                    TenderStatus.EVALUATION,
                    TenderStatus.AWARDED,
                ]),
            )
            .order_by(Tender.created_at.desc())
            .all()
        )

        if not rows:
            await update.message.reply_text("Сіздің белсенді тендерлеріңіз жоқ.")
            return

        STATUS_EMOJI = {
            "published": "🟢",
            "evaluation": "🟡",
            "awarded": "🏆",
        }
        lines = [f"📋 <b>Менің тендерлерім ({user.full_name or user.email}):</b>\n"]
        for t in rows:
            emoji = STATUS_EMOJI.get(t.status.value, "📌")
            lines.append(
                f"{emoji} <b>{t.title}</b>\n"
                f"   Статус: {t.status.value} · ID: {t.id}\n"
                f"   <a href='{APP_URL}/tenders/{t.id}'>Қарау</a>"
            )
        await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error("Error in /mytenders: %s", e)
        await update.message.reply_text("⚠️ Қате орын алды.")
    finally:
        db.close()


# ─────────────────────────── /proposals ─────────────────────────

async def proposals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Supplier's submitted proposals."""
    chat_id = str(update.effective_chat.id)
    db = _get_db()
    try:
        user = _get_linked_user(db, chat_id)
        if not user:
            await update.message.reply_text(
                "⚠️ Аккаунтыңыз байланыстырылмаған.\n"
                "Профильден код алып, <code>/connect КОД</code> деп жіберіңіз.",
                parse_mode="HTML",
            )
            return

        if user.role.value != "supplier":
            await update.message.reply_text("ℹ️ Бұл команда тек SUPPLIER рөлі үшін.")
            return

        rows = (
            db.query(TenderProposal)
            .filter(TenderProposal.supplier_id == user.id)
            .order_by(TenderProposal.created_at.desc())
            .limit(10)
            .all()
        )

        if not rows:
            await update.message.reply_text("Сіздің ұсыныстарыңыз жоқ.")
            return

        STATUS_EMOJI = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}
        lines = ["📋 <b>Менің ұсыныстарым (соңғы 10):</b>\n"]
        for p in rows:
            tender = db.query(Tender).filter(Tender.id == p.tender_id).first()
            tender_title = tender.title if tender else f"Тендер #{p.tender_id}"
            emoji = STATUS_EMOJI.get(p.status.value, "❓")
            lines.append(
                f"{emoji} <b>{tender_title}</b>\n"
                f"   💰 {float(p.price):,.0f} ₸ · {p.delivery_days} күн\n"
                f"   Статус: {p.status.value}"
            )
        await update.message.reply_text("\n\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error("Error in /proposals: %s", e)
        await update.message.reply_text("⚠️ Қате орын алды.")
    finally:
        db.close()


# ─────────────────────────── /status ────────────────────────────

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tender status by ID."""
    if not context.args:
        await update.message.reply_text("Қолдану: /status &lt;tender_id&gt;", parse_mode="HTML")
        return

    try:
        tender_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Тендер ID санды болуы керек.")
        return

    db = _get_db()
    try:
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            await update.message.reply_text(f"Тендер #{tender_id} табылмады.")
            return

        proposals_count = (
            db.query(TenderProposal)
            .filter(TenderProposal.tender_id == tender_id)
            .count()
        )
        deadline_str = tender.deadline.strftime("%Y-%m-%d %H:%M") if tender.deadline else "—"

        STATUS_LABEL = {
            "draft": "📝 Жоба",
            "published": "🟢 Жарияланды",
            "evaluation": "🟡 Бағалауда",
            "awarded": "🏆 Жеңімпаз таңдалды",
            "closed": "🔒 Жабылды",
            "payment_pending": "💳 Төлем күтуде",
        }
        st = STATUS_LABEL.get(tender.status.value, tender.status.value)

        text = (
            f"📋 <b>{tender.title}</b>\n\n"
            f"🆔 ID: {tender.id}\n"
            f"📊 Статус: {st}\n"
            f"💰 Бюджет: {float(tender.budget):,.0f} ₸\n"
            f"📅 Дедлайн: {deadline_str}\n"
            f"📨 Ұсыныстар: {proposals_count}\n"
        )
        if tender.description:
            text += f"\n📝 {tender.description[:200]}{'...' if len(tender.description) > 200 else ''}"

        keyboard = [[InlineKeyboardButton(
            "🔗 Платформада қарау",
            url=f"{APP_URL}/tenders/{tender.id}",
        )]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        logger.error("Error in /status: %s", e)
        await update.message.reply_text("⚠️ Қате орын алды.")
    finally:
        db.close()


# ─────────────────────────── /connect ───────────────────────────

async def connect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Link Telegram account to SmartTender via unique code."""
    if not context.args:
        await update.message.reply_text(
            "Қолдану: /connect &lt;код&gt;\n\n"
            f"Код алу үшін: <a href='{APP_URL}/profile'>Профиль → Telegram байланыстыру</a>",
            parse_mode="HTML",
        )
        return

    code = context.args[0].strip()
    db = _get_db()
    try:
        user = db.query(User).filter(User.telegram_connect_code == code).first()
        if not user:
            await update.message.reply_text(
                "❌ Код табылмады немесе ескірген.\n"
                "Профильде жаңа код жасаңыз."
            )
            return

        user.telegram_chat_id = str(update.effective_chat.id)
        user.telegram_connect_code = None
        db.commit()

        await update.message.reply_text(
            f"✅ <b>Аккаунт сәтті байланыстырылды!</b>\n\n"
            f"Сәлем, {user.full_name or user.email}! 👋\n\n"
            f"Енді барлық хабарландырулар осы чатқа жіберіледі.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Error in /connect: %s", e)
        db.rollback()
        await update.message.reply_text("⚠️ Байланыстыру кезінде қате орын алды.")
    finally:
        db.close()


# ─────────────────────────── inline callbacks ────────────────────

async def inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses (Approve / Reject tender)."""
    query = update.callback_query
    await query.answer()

    chat_id = str(query.from_user.id)
    data: str = query.data or ""

    db = _get_db()
    try:
        user = _get_linked_user(db, chat_id)
        if not user:
            await query.edit_message_text("⚠️ Аккаунтыңыз байланыстырылмаған.")
            return

        if data.startswith("approve_tender:") or data.startswith("reject_tender:"):
            action, tender_id_str = data.split(":", 1)
            tender_id = int(tender_id_str)
            tender = db.query(Tender).filter(Tender.id == tender_id).first()

            if not tender:
                await query.edit_message_text(f"⚠️ Тендер #{tender_id} табылмады.")
                return

            if user.role.value not in ("buyer", "superadmin"):
                await query.edit_message_text("❌ Бұл операцияға рұқсат жоқ.")
                return

            if action == "approve_tender":
                tender.approval_status = "approved"
                db.commit()
                await query.edit_message_text(
                    f"✅ <b>Тендер #{tender_id} бекітілді!</b>\n\n"
                    f"📋 {tender.title}\n"
                    f"<i>SmartTender арқылы бекіттіңіз.</i>",
                    parse_mode="HTML",
                )
            elif action == "reject_tender":
                tender.approval_status = "rejected"
                db.commit()
                await query.edit_message_text(
                    f"❌ <b>Тендер #{tender_id} қабылданбады.</b>\n\n"
                    f"📋 {tender.title}\n"
                    f"<i>SmartTender арқылы қабылданбады.</i>",
                    parse_mode="HTML",
                )
        else:
            await query.edit_message_text("⚠️ Белгісіз команда.")
    except Exception as e:
        logger.error("Error in inline_callback: %s", e)
        db.rollback()
        try:
            await query.edit_message_text("⚠️ Қате орын алды.")
        except Exception:
            pass
    finally:
        db.close()


# ─────────────────────────── factory ────────────────────────────

def create_bot_application() -> Application:
    """Build and configure the bot Application (for webhook/polling mode)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set — bot will be disabled.")
        return None  # type: ignore[return-value]

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tenders", tenders))
    app.add_handler(CommandHandler("mytenders", my_tenders))
    app.add_handler(CommandHandler("proposals", proposals_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("connect", connect_cmd))
    app.add_handler(CallbackQueryHandler(inline_callback))

    return app


def run_polling() -> None:
    """Start the bot in polling mode (used by Docker service)."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    bot_app = create_bot_application()
    if bot_app is None:
        logger.error("Cannot start bot: TELEGRAM_BOT_TOKEN not configured.")
        return
    logger.info("Starting SmartTender Bot in polling mode …")
    bot_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_polling()
