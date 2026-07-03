"""Seed / sync demo users."""

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.database import SessionLocal
from app.models.department import Department
from app.models.user import User, UserRole

DEMO_USERS = [
    ("admin@smarttender.kz", "admin123", "Әкімші", UserRole.SUPERADMIN, True),
    ("manager@smarttender.kz", "manager123", "Сатып алушы (Buyer)", UserRole.BUYER, True),
    ("head@smarttender.kz", "head123", "Бөлім басшысы", UserRole.DEPARTMENT_HEAD, True),
    ("employee@smarttender.kz", "employee123", "Қызметкер", UserRole.EMPLOYEE, True),
    ("supplier@smarttender.kz", "supplier123", "Жеткізуші", UserRole.SUPPLIER, False),
]


def seed() -> None:
    db = SessionLocal()
    try:
        dept = db.query(Department).filter(Department.name == "IT бөлімі").first()
        if not dept:
            dept = Department(name="IT бөлімі", budget_limit=Decimal("50000000"))
            db.add(dept)
            db.flush()

        for email, password, full_name, role, in_dept in DEMO_USERS:
            user = db.query(User).filter(User.email == email).first()
            hashed = get_password_hash(password)
            if user:
                user.hashed_password = hashed
                user.full_name = full_name
                user.role = role
                user.is_active = True
                user.is_verified = True
                user.department_id = dept.id if in_dept else None
            else:
                db.add(
                    User(
                        email=email,
                        hashed_password=hashed,
                        full_name=full_name,
                        role=role,
                        department_id=dept.id if in_dept else None,
                        is_active=True,
                        is_verified=True,
                    )
                )

        db.commit()
        print("Demo users synced (passwords updated)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
