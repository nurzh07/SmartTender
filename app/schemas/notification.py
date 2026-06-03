from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationType


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    message: str
    is_read: bool
    channel: NotificationChannel
    sent_at: datetime

    class Config:
        from_attributes = True
