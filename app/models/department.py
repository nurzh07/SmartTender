from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_limit = Column(Numeric(15, 2), default=0)
    head_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    users = relationship("User", back_populates="department")
