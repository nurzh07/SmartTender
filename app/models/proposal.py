from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TenderProposal(Base):
    __tablename__ = "tender_proposals"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    delivery_days = Column(Integer, nullable=False)
    file_url = Column(String)
    score = Column(Integer, default=0)
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tender = relationship("Tender", back_populates="proposals")
    supplier = relationship("User")
