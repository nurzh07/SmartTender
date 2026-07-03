"""
Celery tasks for BIN verification retry.

Daily job: retry failed BIN verifications for users where bin is set but bin_verified=False.
"""

import logging
from datetime import datetime

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def retry_failed_bin_verifications() -> dict:
    """
    Daily task: retry BIN verification for users with unverified BINs.
    Runs at 10:00 AM daily.
    """
    from app.database import SessionLocal
    from app.models.user import User
    from app.services.bin_verification import verify_bin

    db = SessionLocal()
    retried = 0
    verified = 0
    errors = 0

    try:
        # Find users with BIN but not verified
        users = (
            db.query(User)
            .filter(
                User.bin.isnot(None),  # type: ignore[attr-defined]
                User.bin_verified.is_(False),  # type: ignore[attr-defined]
            )
            .all()
        )

        logger.info("BIN retry: found %d unverified users", len(users))

        for user in users:
            retried += 1
            try:
                result = verify_bin(user.bin)  # type: ignore[attr-defined]
                if result.valid:
                    user.bin_verified = True  # type: ignore[attr-defined]
                    user.company_official_name = result.company_name  # type: ignore[attr-defined]
                    user.company_registration_date = result.registration_date  # type: ignore[attr-defined]
                    user.company_status = result.company_status  # type: ignore[attr-defined]
                    user.bin_verified_at = datetime.utcnow()  # type: ignore[attr-defined]
                    db.commit()
                    db.refresh(user)
                    verified += 1
                    logger.info("BIN verified for user %d: %s", user.id, result.company_name)
                else:
                    logger.debug("BIN still invalid for user %d: %s", user.id, result.error)
            except Exception as exc:
                errors += 1
                db.rollback()
                logger.error("BIN retry error for user %d: %s", user.id, exc)

    finally:
        db.close()

    return {
        "status": "done",
        "retried": retried,
        "verified": verified,
        "errors": errors,
    }
