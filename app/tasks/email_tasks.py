import logging
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any

from app.config import get_settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _log_email_to_file(to: str, subject: str, body: str) -> None:
    os.makedirs("uploads", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    with open(f"uploads/email_{timestamp}.txt", "w", encoding="utf-8") as fh:
        fh.write(f"To: {to}\n")
        fh.write(f"Subject: {subject}\n")
        fh.write("\n")
        fh.write(body)


def _send_smtp(to: str, subject: str, body: str) -> tuple[bool, str | None]:
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USER:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        return True, None
    except Exception as exc:
        reason = str(exc)
        logger.warning("SMTP failed (%s), logging only: %s", reason, subject)
        _log_email_to_file(to, subject, body)
        return False, reason


def _deliver_email(to: str, subject: str, body: str) -> dict[str, Any]:
    sent, reason = _send_smtp(to, subject, body)
    logger.info("Email [%s] to %s: %s", "sent" if sent else "logged", to, subject)
    if not sent:
        print(f"\n{'='*60}")
        print(f"[EMAIL LOG] To: {to}")
        print(f"[EMAIL LOG] Subject: {subject}")
        print(f"[EMAIL LOG] Body:\n{body}")
        print(f"{'='*60}\n")
    return {
        "status": "sent" if sent else "logged",
        "email": to,
        "reason": reason,
    }


@celery_app.task
def send_email_notification(email: str, subject: str, message: str) -> dict:
    return _deliver_email(email, subject, message)


@celery_app.task
def send_bulk_emails(recipients: list[str], subject: str, message: str) -> dict:
    """Қызметкерлерге жаппай хат жіберу (фондық режим, main thread бұғаттамайды)."""
    sent = 0
    for email in recipients:
        result = _deliver_email(email, subject, message)
        if result["status"] == "sent":
            sent += 1
        else:
            logger.info("Bulk email logged for %s: %s", email, subject)
    return {"status": "completed", "sent": sent, "total": len(recipients)}


@celery_app.task
def send_password_reset_email(email: str, reset_link: str) -> dict:
    subject = "SmartTender — құпия сөзді қалпына келтіру"
    message = (
        "Сәлем!\n\n"
        "SmartTender-ге құпия сөзді қалпына келтіру сұрауы қабылданды.\n"
        "Келесі сілтеме арқылы жаңа құпия сөз қойыңыз:\n\n"
        f"{reset_link}\n\n"
        "Бұл сілтеме 1 сағат бойы жарамды.\n"
        "Егер сіз бұл сұрауды жібермеген болсаңыз, бұл хатты елемеуге болады."
    )
    return _deliver_email(email, subject, message)


@celery_app.task
def send_verification_email(email: str, verify_link: str) -> dict:
    subject = "SmartTender — email растау"
    message = (
        "SmartTender-ге тіркелгеніңіз үшін рахмет!\n"
        "Email-ді растау үшін сілтемеге өтіңіз (24 сағат жарамды):\n"
        f"{verify_link}"
    )
    return _deliver_email(email, subject, message)


@celery_app.task
def send_welcome_email(email: str, username: str) -> dict:
    """Welcome email after successful registration"""
    subject = "SmartTender — Тіркелу сәтті өтті!"
    message = (
        f"Сәлем, {username}!\n\n"
        "Сіз SmartTender платформасына сәтті тіркелдіңіз.\n"
        "Біздің платформада тендерлерге қатысу, ұсыныстар жіберу және "
        "басқа да мүмкіндіктерді пайдалана аласыз.\n\n"
        "Платформаға кіру үшін: http://localhost:3000/login\n\n"
        "Сұрақтарыңыз болса, бізге хабарласыңыз.\n\n"
        "SmartTender командасы"
    )
    return _deliver_email(email, subject, message)


@celery_app.task
def send_tender_published_email(supplier_emails: list[str], tender_title: str, tender_id: int) -> dict:
    """Tender published → email to ALL suppliers"""
    subject = f"SmartTender — Жаңа тендер: {tender_title}"
    message = (
        f"Жаңа тендер жарияланды:\n"
        f"Атауы: {tender_title}\n"
        f"ID: {tender_id}\n"
        f"Ұсыныс жіберу үшін SmartTender платформасына кіріңіз."
    )
    sent_count = 0
    for email in supplier_emails:
        result = _deliver_email(email, subject, message)
        if result["status"] == "sent":
            sent_count += 1
    return {"status": "completed", "sent": sent_count, "total": len(supplier_emails)}


@celery_app.task
def send_new_proposal_email(buyer_email: str, tender_title: str, supplier_name: str) -> dict:
    """New proposal received → email to BUYER"""
    subject = f"SmartTender — Жаңа ұсыныс: {tender_title}"
    message = (
        f"Тендерге жаңа ұсыныс келді:\n"
        f"Тендер: {tender_title}\n"
        f"Жеткізуші: {supplier_name}\n"
        f"Ұсыныстарды қарау үшін SmartTender платформасына кіріңіз."
    )
    return _deliver_email(buyer_email, subject, message)


@celery_app.task
def send_deadline_reminder_3days(recipient_emails: list[str], tender_title: str, deadline: str) -> dict:
    """Deadline -3 days -> reminder to buyer + all participants"""
    from app.services.email_utils import send_deadline_reminder_email as send_deadline_reminder_email_resend
    
    subject = f"SmartTender — Дедлайн ескерту (3 күн қалды): {tender_title}"
    message = (
        f"Тендер дедлайнына 3 күн қалды:\n"
        f"Тендер: {tender_title}\n"
        f"Дедлайн: {deadline}\n"
        f"Уақытты өткізіп алмаңыз!"
    )
    sent_count = 0
    for email in recipient_emails:
        result = _deliver_email(email, subject, message)
        if result["status"] == "sent":
            sent_count += 1
        
        # Send with Resend
        send_deadline_reminder_email_resend(email, tender_title, deadline, 3)
    return {"status": "completed", "sent": sent_count, "total": len(recipient_emails)}


@celery_app.task
def send_deadline_reminder_1day(recipient_emails: list[str], tender_title: str, deadline: str) -> dict:
    """Deadline -1 day -> final reminder"""
    from app.services.email_utils import send_deadline_reminder_email as send_deadline_reminder_email_resend
    
    subject = f"SmartTender — Дедлайн ескерту (1 күн қалды): {tender_title}"
    message = (
        f"Тендер дедлайнына 1 күн қалды:\n"
        f"Тендер: {tender_title}\n"
        f"Дедлайн: {deadline}\n"
        f"Жедел әрекет етіңіз!"
    )
    sent_count = 0
    for email in recipient_emails:
        result = _deliver_email(email, subject, message)
        if result["status"] == "sent":
            sent_count += 1
        
        # Send with Resend
        send_deadline_reminder_email_resend(email, tender_title, deadline, 1)
    return {"status": "completed", "sent": sent_count, "total": len(recipient_emails)}


@celery_app.task
def send_winner_selected_email(winner_email: str, tender_title: str, loser_emails: list[str]) -> dict:
    """Winner selected → "Congrats" to winner, "Sorry" to others"""
    # Winner email
    subject_winner = f"SmartTender — Құттықтаймыз! Сіз жеңдіңіз: {tender_title}"
    message_winner = (
        f"Құттықтаймыз! Сіз тендерді жеңдіңіз:\n"
        f"Тендер: {tender_title}\n"
        f"Келесі қадамдар туралы ақпаратты кейін аласыз."
    )
    sent_winner = _deliver_email(winner_email, subject_winner, message_winner)["status"] == "sent"

    # Loser emails
    subject_loser = f"SmartTender — Қайғырмыз, сіз жеңілдіңіз: {tender_title}"
    message_loser = (
        f"Қайғырмыз, бұл тендерді жеңе алмадыңыз:\n"
        f"Тендер: {tender_title}\n"
        f"Басқа мүмкіндіктерді көріңіз."
    )
    sent_losers = 0
    for email in loser_emails:
        result = _deliver_email(email, subject_loser, message_loser)
        if result["status"] == "sent":
            sent_losers += 1

    return {
        "status": "completed",
        "winner_sent": sent_winner,
        "losers_sent": sent_losers,
        "losers_total": len(loser_emails),
    }


@celery_app.task
def send_tender_closed_email(buyer_email: str, tender_title: str, pdf_url: str) -> dict:
    """Tender closed → PDF report sent to buyer's email"""
    subject = f"SmartTender — Тендер жабылды: {tender_title}"
    message = (
        f"Тендер сәтті жабылды:\n"
        f"Тендер: {tender_title}\n"
        f"Есепті жүктеу: {pdf_url}\n"
        f"Рахмет SmartTender-ді қолданғаныңыз үшін!"
    )
    return _deliver_email(buyer_email, subject, message)
