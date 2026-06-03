from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import pg_enum
import enum


class TenderStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    EVALUATION = "evaluation"
    AWARDED = "awarded"
    CLOSED = "closed"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    budget = Column(Numeric(15, 2), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(pg_enum(TenderStatus, "tenderstatus"), default=TenderStatus.DRAFT, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    external_id = Column(String, nullable=True, index=True)
    approval_status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_tenders_status_deadline', 'status', 'deadline'),
        Index('ix_tenders_category_status', 'category_id', 'status'),
    )

    creator = relationship("User")
    category = relationship("Category", back_populates="tenders")
    proposals = relationship("TenderProposal", back_populates="tender")
    approval_steps = relationship("ApprovalWorkflow", back_populates="tender")
