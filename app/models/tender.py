from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
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
    status = Column(SQLEnum(TenderStatus), default=TenderStatus.DRAFT, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User")
    category = relationship("Category")
    proposals = relationship("TenderProposal", back_populates="tender")
