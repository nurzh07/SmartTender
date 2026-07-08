from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class TenderWatchlist(Base):
    """Тендер бақылау тізімі"""
    __tablename__ = "tender_watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tender_id = Column(String, nullable=False)  # Сыртқы тендер ID
    source = Column(String, nullable=False)  # "goszakupki" немесе "samruk_kazyna"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlist")
