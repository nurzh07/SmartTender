from app.tasks.celery_app import celery_app


@celery_app.task
def send_email_notification(email: str, subject: str, message: str):
    """Отправка email уведомления (заглушка для демонстрации)"""
    print(f"Sending email to {email}")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    # Здесь будет реальная отправка через SMTP или email сервис
    return {"status": "sent", "email": email}


@celery_app.task
def send_tender_notification(tender_id: int, supplier_emails: list):
    """Отправка уведомления о новом тендере поставщикам"""
    for email in supplier_emails:
        send_email_notification.delay(
            email=email,
            subject=f"Новый тендер #{tender_id}",
            message="Опубликован новый тендер. Подайте ваше предложение."
        )
    return {"status": "queued", "recipients": len(supplier_emails)}
