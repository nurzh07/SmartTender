from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import pg_enum
import enum


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TenderProposal(Base):
    __tablename__ = "tender_proposals"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    price = Column(Numeric(15, 2), nullable=False)
    delivery_days = Column(Integer, nullable=False)
    file_url = Column(String)
    score = Column(Integer, default=0)
    status = Column(pg_enum(ProposalStatus, "proposalstatus"), default=ProposalStatus.PENDING, nullable=False, index=True)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_proposals_tender_supplier', 'tender_id', 'supplier_id'),
        Index('ix_proposals_tender_status', 'tender_id', 'status'),
    )

    tender = relationship("Tender", back_populates="proposals")
    supplier = relationship("User")
