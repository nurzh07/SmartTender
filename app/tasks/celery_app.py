from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "smarttender",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks",
        "app.tasks.goszakupki_tasks",
        "app.tasks.bin_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # ── Reports ──────────────────────────────────────────────
        "deadline-reminders-daily": {
            "task": "app.tasks.report_tasks.check_deadline_reminders",
            "schedule": crontab(hour=9, minute=0),
        },
        "monthly-pdf-report": {
            "task": "app.tasks.report_tasks.generate_monthly_pdf_report",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),
            "kwargs": {"period": "auto", "user_id": None},
        },
        "monthly-budget-analytics": {
            "task": "app.tasks.report_tasks.generate_budget_analytics",
            "schedule": crontab(day_of_month=1, hour=7, minute=0),
            "kwargs": {"period": "auto", "user_id": None},
        },
        "monthly-supplier-ratings": {
            "task": "app.tasks.report_tasks.generate_supplier_ratings_excel",
            "schedule": crontab(day_of_month=1, hour=8, minute=0),
            "kwargs": {"period": "auto", "user_id": None},
        },
        # ── Goszakupki ───────────────────────────────────────────
        "goszakupki-import-daily": {
            "task": "app.tasks.goszakupki_tasks.import_open_tenders_from_goszakupki",
            "schedule": crontab(hour=3, minute=0),
            "kwargs": {"limit": 20},
        },
        # ── BIN Verification retry ───────────────────────────────
        "bin-verification-retry-daily": {
            "task": "app.tasks.bin_tasks.retry_failed_bin_verifications",
            "schedule": crontab(hour=10, minute=0),
        },
    },
)
