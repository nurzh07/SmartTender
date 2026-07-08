from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Permission(Base):
    """Құқықтар"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    module = Column(String(50), nullable=False)  # tenders, users, reports, etc.
    action = Column(String(50), nullable=False)  # create, read, update, delete, approve
    resource = Column(String(50), nullable=True)  # tender, user, report, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    """Рөл-Құқық байланысы"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)  # superadmin, buyer, supplier, etc.
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True)  # True = құқық бар, False = жоқ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    permission = relationship("Permission")


class UserPermission(Base):
    """Пайдаланушы-Құқық байланысы (жеке құқықтар)"""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    permission = relationship("Permission")
    user = relationship("User")
