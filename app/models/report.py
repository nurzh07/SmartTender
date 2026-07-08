from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ReportType(str, enum.Enum):
    TENDER_SUMMARY = "tender_summary"
    SUPPLIER_PERFORMANCE = "supplier_performance"
    PROCUREMENT_REPORT = "procurement_report"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(SQLEnum(ReportType), index=True)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # pdf, xlsx
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = relationship("User", back_populates="reports")
