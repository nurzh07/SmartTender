"""Seed / sync demo users and sample data."""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.database import SessionLocal
from app.models.approval import ApprovalStatus, ApprovalWorkflow
from app.models.category import Category
from app.models.department import Department
from app.models.proposal import ProposalStatus, TenderProposal
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole

DEMO_USERS = [
    ("admin@smarttender.kz", "admin123", "Әкімші", UserRole.SUPERADMIN, True),
    ("manager@smarttender.kz", "manager123", "Сатып алу менеджері", UserRole.PROCUREMENT_MANAGER, True),
    ("head@smarttender.kz", "head123", "Бөлім басшысы", UserRole.DEPARTMENT_HEAD, True),
    ("employee@smarttender.kz", "employee123", "Қызметкер", UserRole.EMPLOYEE, True),
    ("supplier@smarttender.kz", "supplier123", "Жеткізуші", UserRole.SUPPLIER, False),
]


def _get_user(db, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def _upsert_tender(
    db,
    *,
    title: str,
    creator: User,
    status: TenderStatus,
    approval_status: str,
    budget: Decimal,
    deadline: datetime,
    category_id: int | None,
    description: str,
) -> Tender:
    tender = db.query(Tender).filter(Tender.title == title).first()
    if tender:
        tender.description = description
        tender.budget = budget
        tender.deadline = deadline
        tender.status = status
        tender.approval_status = approval_status
        tender.category_id = category_id
        tender.created_by = creator.id
    else:
        tender = Tender(
            title=title,
            description=description,
            budget=budget,
            deadline=deadline,
            status=status,
            approval_status=approval_status,
            category_id=category_id,
            created_by=creator.id,
        )
        db.add(tender)
    db.flush()
    return tender


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

        employee = _get_user(db, "employee@smarttender.kz")
        manager = _get_user(db, "manager@smarttender.kz")
        supplier = _get_user(db, "supplier@smarttender.kz")
        if not employee or not manager or not supplier:
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

        # 1) Қызметкердің жоба өтінімі — employee бекітуге жібереді
        draft_tender = _upsert_tender(
            db,
            title="Қызметкер өтінімі — кеңсе мебелі",
            creator=employee,
            status=TenderStatus.DRAFT,
            approval_status="draft",
            budget=Decimal("3500000"),
            deadline=deadline,
            category_id=cat_office.id,
            description="Жаңа кеңсе үшін үстел мен орындық сатып алу",
        )

        # 2) Бекіту процесінде — бөлім басшысы бекітеді
        pending_tender = _upsert_tender(
            db,
            title="Бекіту күтуде — ноутбук",
            creator=employee,
            status=TenderStatus.DRAFT,
            approval_status="pending_approval",
            budget=Decimal("8500000"),
            deadline=deadline + timedelta(days=7),
            category_id=cat_it.id,
            description="Әзірлеушілерге 10 дана ноутбук",
        )
        db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.tender_id == pending_tender.id
        ).delete()
        db.add_all(
            [
                ApprovalWorkflow(
                    tender_id=pending_tender.id,
                    step=1,
                    status=ApprovalStatus.PENDING,
                ),
                ApprovalWorkflow(
                    tender_id=pending_tender.id,
                    step=2,
                    status=ApprovalStatus.PENDING,
                ),
            ]
        )

        # 3) Жарияланған тендер — жеткізуші ұсыныс жібереді
        published_tender = _upsert_tender(
            db,
            title="Жарияланған — принтерлер",
            creator=manager,
            status=TenderStatus.PUBLISHED,
            approval_status="approved",
            budget=Decimal("2500000"),
            deadline=deadline + timedelta(days=21),
            category_id=cat_office.id,
            description="Кеңсе принтерлері — 5 дана",
        )

        # Ескі демо тендерлерді жаңарту
        _upsert_tender(
            db,
            title="Ноутбук сатып алу",
            creator=manager,
            status=TenderStatus.PUBLISHED,
            approval_status="approved",
            budget=Decimal("12000000"),
            deadline=deadline,
            category_id=cat_it.id,
            description="20 дана ноутбук",
        )

        existing_proposal = (
            db.query(TenderProposal)
            .filter(
                TenderProposal.tender_id == published_tender.id,
                TenderProposal.supplier_id == supplier.id,
            )
            .first()
        )
        if not existing_proposal:
            db.add(
                TenderProposal(
                    tender_id=published_tender.id,
                    supplier_id=supplier.id,
                    price=Decimal("2300000"),
                    delivery_days=14,
                    score=87,
                    status=ProposalStatus.PENDING,
                    comment="HP LaserJet, 1 жыл кепілдік",
                )
            )

        db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.tender_id == draft_tender.id
        ).delete()
        db.commit()
        print("Demo tenders synced (employee draft, pending approval, published lot)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
