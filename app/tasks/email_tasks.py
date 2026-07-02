import logging
import smtplib
from email.mime.text import MIMEText

from app.config import get_settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _send_smtp(to: str, subject: str, body: str) -> bool:
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
        return True
    except Exception as exc:
        logger.warning("SMTP failed (%s), logging only: %s", exc, subject)
        return False


@celery_app.task
def send_email_notification(email: str, subject: str, message: str) -> dict:
    sent = _send_smtp(email, subject, message)
    logger.info("Email [%s] to %s: %s", "sent" if sent else "logged", email, subject)
    if not sent:
        print(f"[EMAIL] To: {email} | {subject}\n{message}")
    return {"status": "sent" if sent else "logged", "email": email}


@celery_app.task
def send_bulk_emails(recipients: list[str], subject: str, message: str) -> dict:
    """Қызметкерлерге жаппай хат жіберу (фондық режим, main thread бұғаттамайды)."""
    sent = 0
    for email in recipients:
        if _send_smtp(email, subject, message):
            sent += 1
        else:
            logger.info("Bulk email logged for %s: %s", email, subject)
    return {"status": "completed", "sent": sent, "total": len(recipients)}


@celery_app.task
def send_password_reset_email(email: str, reset_link: str) -> dict:
    subject = "SmartTender — парольді қалпына келтіру"
    message = f"Сілтеме (1 сағат жарамды):\n{reset_link}"
    sent = _send_smtp(email, subject, message)
    if not sent:
        print(f"[RESET] {email}: {reset_link}")
    return {"status": "sent" if sent else "logged", "email": email}


@celery_app.task
def send_verification_email(email: str, verify_link: str) -> dict:
    subject = "SmartTender — email растау"
    message = (
        "SmartTender-ге тіркелгеніңіз үшін рахмет!\n"
        "Email-ді растау үшін сілтемеге өтіңіз (24 сағат жарамды):\n"
        f"{verify_link}"
    )
    sent = _send_smtp(email, subject, message)
    if not sent:
        print(f"[VERIFY] {email}: {verify_link}")
    return {"status": "sent" if sent else "logged", "email": email}


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
        if _send_smtp(email, subject, message):
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
    sent = _send_smtp(buyer_email, subject, message)
    return {"status": "sent" if sent else "logged", "email": buyer_email}


@celery_app.task
def send_deadline_reminder_3days(recipient_emails: list[str], tender_title: str, deadline: str) -> dict:
    """Deadline -3 days → reminder to buyer + all participants"""
    subject = f"SmartTender — Дедлайн ескерту (3 күн қалды): {tender_title}"
    message = (
        f"Тендер дедлайнына 3 күн қалды:\n"
        f"Тендер: {tender_title}\n"
        f"Дедлайн: {deadline}\n"
        f"Уақытты өткізіп алмаңыз!"
    )
    sent_count = 0
    for email in recipient_emails:
        if _send_smtp(email, subject, message):
            sent_count += 1
    return {"status": "completed", "sent": sent_count, "total": len(recipient_emails)}


@celery_app.task
def send_deadline_reminder_1day(recipient_emails: list[str], tender_title: str, deadline: str) -> dict:
    """Deadline -1 day → final reminder"""
    subject = f"SmartTender — Дедлайн ескерту (1 күн қалды): {tender_title}"
    message = (
        f"Тендер дедлайнына 1 күн қалды:\n"
        f"Тендер: {tender_title}\n"
        f"Дедлайн: {deadline}\n"
        f"Жедел әрекет етіңіз!"
    )
    sent_count = 0
    for email in recipient_emails:
        if _send_smtp(email, subject, message):
            sent_count += 1
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
    sent_winner = _send_smtp(winner_email, subject_winner, message_winner)

    # Loser emails
    subject_loser = f"SmartTender — Қайғырмыз, сіз жеңілдіңіз: {tender_title}"
    message_loser = (
        f"Қайғырмыз, бұл тендерді жеңе алмадыңыз:\n"
        f"Тендер: {tender_title}\n"
        f"Басқа мүмкіндіктерді көріңіз."
    )
    sent_losers = 0
    for email in loser_emails:
        if _send_smtp(email, subject_loser, message_loser):
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
    sent = _send_smtp(buyer_email, subject, message)
    return {"status": "sent" if sent else "logged", "email": buyer_email}
