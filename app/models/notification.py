import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import pg_enum


class NotificationType(str, enum.Enum):
    TENDER_PUBLISHED = "tender_published"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    DEADLINE_REMINDER = "deadline_reminder"
    TENDER_AWARDED = "tender_awarded"
    PASSWORD_RESET = "password_reset"
    REPORT_READY = "report_ready"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    IN_APP = "in_app"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(pg_enum(NotificationType, "notificationtype"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    channel = Column(pg_enum(NotificationChannel, "notificationchannel"), default=NotificationChannel.IN_APP)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
