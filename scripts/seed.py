"""Seed demo data for development and demos (week 1-2)."""

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


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@smarttender.kz").first():
            print("Seed skipped: data already exists")
            return

        dept = Department(name="IT бөлімі", budget_limit=Decimal("50000000"))
        db.add(dept)
        db.flush()

        admin = User(
            email="admin@smarttender.kz",
            hashed_password=get_password_hash("admin123"),
            full_name="Әкімші",
            role=UserRole.SUPERADMIN,
            department_id=dept.id,
        )
        manager = User(
            email="manager@smarttender.kz",
            hashed_password=get_password_hash("manager123"),
            full_name="Сатып алу менеджері",
            role=UserRole.PROCUREMENT_MANAGER,
            department_id=dept.id,
        )
        supplier = User(
            email="supplier@smarttender.kz",
            hashed_password=get_password_hash("supplier123"),
            full_name="Жеткізуші",
            role=UserRole.SUPPLIER,
        )
        db.add_all([admin, manager, supplier])
        db.flush()

        cat_it = Category(name="IT жабдық", description="Компьютерлер, серверлер")
        cat_office = Category(name="Кеңсе", description="Кеңсе тауарлары")
        db.add_all([cat_it, cat_office])
        db.flush()

        deadline = datetime.now(timezone.utc) + timedelta(days=14)
        tenders = [
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
        db.add_all(tenders)
        db.commit()
        print("Seed completed: demo users and tenders created")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
