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
