import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import pg_enum


class ReportType(str, enum.Enum):
    MONTHLY_TENDERS_PDF = "monthly_tenders_pdf"
    SUPPLIER_RATINGS_EXCEL = "supplier_ratings_excel"
    BUDGET_ANALYTICS = "budget_analytics"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(pg_enum(ReportType, "reporttype"), nullable=False)
    period = Column(String, nullable=False)
    file_url = Column(String)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    generator = relationship("User")
