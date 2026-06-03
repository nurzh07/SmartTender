import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import pg_enum


class ApprovalStep(int, enum.Enum):
    DEPARTMENT_HEAD = 1
    PROCUREMENT_MANAGER = 2


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflow"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    step = Column(Integer, nullable=False)
    status = Column(pg_enum(ApprovalStatus, "approvalstatus"), default=ApprovalStatus.PENDING, nullable=False)
    comment = Column(Text)
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tender = relationship("Tender", back_populates="approval_steps")
    approver = relationship("User")
