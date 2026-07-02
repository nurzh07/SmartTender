from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import pg_enum
import enum


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    BUYER = "buyer"
    PROCUREMENT_MANAGER = "procurement_manager"
    DEPARTMENT_HEAD = "department_head"
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(pg_enum(UserRole, "userrole"), default=UserRole.EMPLOYEE, nullable=False)
    full_name = Column(String)
    telegram_chat_id = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    department = relationship(
        "Department",
        back_populates="users",
        foreign_keys=[department_id],
    )
