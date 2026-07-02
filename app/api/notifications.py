from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.schemas.notification import BulkEmailRequest, NotificationResponse
from app.tasks.email_tasks import send_bulk_emails

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def list_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    return q.order_by(Notification.sent_at.desc()).limit(50).all()


@router.post("/bulk-email")
async def queue_bulk_email(
    data: BulkEmailRequest,
    _: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.BUYER)),
):
    task = send_bulk_emails.delay(
        recipients=[str(email) for email in data.recipients],
        subject=data.subject,
        message=data.message,
    )
    return {"status": "queued", "task_id": task.id, "recipients": len(data.recipients)}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if n:
        n.is_read = True
        db.commit()
        db.refresh(n)
    return n
