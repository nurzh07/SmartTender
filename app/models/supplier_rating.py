from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SupplierRating(Base):
    __tablename__ = "supplier_ratings"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    quality_score = Column(Numeric(5, 2), default=0)
    delivery_score = Column(Numeric(5, 2), default=0)
    avg_score = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("User")
    tender = relationship("Tender")
