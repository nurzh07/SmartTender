from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationType
from app.models.user import User, UserRole


def create_in_app_notification(
    db: Session,
    user_id: int,
    ntype: NotificationType,
    message: str,
    channel: NotificationChannel = NotificationChannel.IN_APP,
) -> Notification:
    n = Notification(user_id=user_id, type=ntype, message=message, channel=channel)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_supplier_users(db: Session) -> list[User]:
    return db.query(User).filter(User.role == UserRole.SUPPLIER, User.is_active.is_(True)).all()


def queue_tender_published(db: Session, tender_id: int, title: str) -> None:
    from app.tasks.notification_tasks import notify_tender_published

    suppliers = get_supplier_users(db)
    emails = [u.email for u in suppliers]
    user_ids = [u.id for u in suppliers]
    notify_tender_published.delay(tender_id, title, emails, user_ids)


def queue_approval_result(db: Session, user_id: int, approved: bool, tender_title: str) -> None:
    from app.tasks.notification_tasks import notify_approval_result

    notify_approval_result.delay(user_id, approved, tender_title)


def queue_tender_awarded(db: Session, tender_id: int, title: str, winner_name: str) -> None:
    from app.tasks.notification_tasks import notify_tender_awarded

    participant_ids = [u.id for u in db.query(User).filter(User.is_active.is_(True)).all()]
    notify_tender_awarded.delay(tender_id, title, winner_name, participant_ids)
