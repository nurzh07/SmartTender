from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SupplierRating(Base):
    __tablename__ = "supplier_ratings"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Рейтинг баллары (1-5)
    quality_score = Column(Numeric(5, 2), default=0)
    delivery_score = Column(Numeric(5, 2), default=0)
    communication_score = Column(Numeric(5, 2), default=0)
    price_score = Column(Numeric(5, 2), default=0)
    avg_score = Column(Numeric(5, 2), default=0)
    
    # Пікір
    review = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    supplier = relationship("User", foreign_keys=[supplier_id])
    buyer = relationship("User", foreign_keys=[buyer_id])
    tender = relationship("Tender")


class SupplierPortfolio(Base):
    """Жеткізушілер портфолиосы"""
    __tablename__ = "supplier_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Жоба ақпараты
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text, nullable=True)
    project_value = Column(Numeric(15, 2), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Клиент ақпараты
    client_name = Column(String(255), nullable=True)
    client_contact = Column(String(255), nullable=True)
    
    # Файлдар
    documents = Column(Text, nullable=True)  # JSON format
    
    # Статус
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    supplier = relationship("User")


class SupplierCertification(Base):
    """Жеткізушілер сертификаттары"""
    __tablename__ = "supplier_certifications"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Сертификат ақпараты
    certification_name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=False)
    certificate_number = Column(String(255), nullable=True)
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Файл
    document_url = Column(String(500), nullable=True)
    
    # Статус
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    supplier = relationship("User")

