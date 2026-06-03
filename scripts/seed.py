"""Seed / sync demo users and sample data."""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.database import SessionLocal
from app.models.category import Category
from app.models.department import Department
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole

DEMO_USERS = [
    ("admin@smarttender.kz", "admin123", "Әкімші", UserRole.SUPERADMIN, True),
    ("manager@smarttender.kz", "manager123", "Сатып алу менеджері", UserRole.PROCUREMENT_MANAGER, True),
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
                    )
                )

        db.commit()
        print("Demo users synced (passwords updated)")

        manager = db.query(User).filter(User.email == "manager@smarttender.kz").first()
        if not manager:
            return

        if db.query(Tender).count() > 0:
            print("Tenders already exist, skip")
            return

        cat_it = db.query(Category).filter(Category.name == "IT жабдық").first()
        if not cat_it:
            cat_it = Category(name="IT жабдық", description="Компьютерлер, серверлер")
            db.add(cat_it)
        cat_office = db.query(Category).filter(Category.name == "Кеңсе").first()
        if not cat_office:
            cat_office = Category(name="Кеңсе", description="Кеңсе тауарлары")
            db.add(cat_office)
        db.flush()

        deadline = datetime.now(timezone.utc) + timedelta(days=14)
        db.add_all(
            [
                Tender(
                    title="Ноутбук сатып алу",
                    description="20 дана ноутбук",
                    budget=Decimal("12000000"),
                    deadline=deadline,
                    status=TenderStatus.PUBLISHED,
                    category_id=cat_it.id,
                    created_by=manager.id,
                ),
                Tender(
                    title="Принтерлер",
                    description="Кеңсе принтерлері",
                    budget=Decimal("2500000"),
                    deadline=deadline + timedelta(days=7),
                    status=TenderStatus.DRAFT,
                    category_id=cat_office.id,
                    created_by=manager.id,
                ),
            ]
        )
        db.commit()
        print("Sample tenders created")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
