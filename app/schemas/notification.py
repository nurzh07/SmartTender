from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

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


class BulkEmailRequest(BaseModel):
    recipients: list[EmailStr] = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
