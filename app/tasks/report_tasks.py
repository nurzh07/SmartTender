import io
from datetime import datetime

from app.config import get_settings
from app.database import SessionLocal
from app.models.report import Report, ReportType
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.services.storage import save_report_file
from app.tasks.celery_app import celery_app

settings = get_settings()


@celery_app.task(bind=True)
def generate_monthly_pdf_report(self, period: str = "auto", user_id: int | None = None) -> dict:
    if period == "auto":
        period = datetime.now().strftime("%Y-%m")
    db = SessionLocal()
    try:
        tenders = db.query(Tender).all()
        content = _build_pdf_bytes(period, tenders)
        filename = f"tenders_{period}.pdf"
        file_url = save_report_file(filename, content)

        report = Report(
            report_type=ReportType.MONTHLY_TENDERS_PDF,
            period=period,
            file_url=file_url,
            generated_by=user_id,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report_id": report.id, "file_url": file_url}
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_supplier_ratings_excel(self, period: str, user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        from app.models.supplier_rating import SupplierRating

        ratings = db.query(SupplierRating).all()
        content = _build_excel_bytes(ratings)
        filename = f"supplier_ratings_{period}.xlsx"
        file_url = save_report_file(filename, content)

        report = Report(
            report_type=ReportType.SUPPLIER_RATINGS_EXCEL,
            period=period,
            file_url=file_url,
            generated_by=user_id,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report_id": report.id, "file_url": file_url}
    finally:
        db.close()


@celery_app.task
def check_deadline_reminders() -> dict:
    from datetime import UTC, timedelta

    from app.models.proposal import TenderProposal
    from app.models.tender import TenderStatus
    from app.services.notifications import get_buyer_email
    from app.tasks.notification_tasks import notify_deadline_reminder

    db = SessionLocal()
    sent = 0
    try:
        now = datetime.now(UTC)
        tenders = (
            db.query(Tender)
            .filter(Tender.status == TenderStatus.PUBLISHED)
            .all()
        )

        for t in tenders:
            if not t.deadline:
                continue
            days = (t.deadline.replace(tzinfo=UTC) - now).days
            if days not in (3, 1):
                continue

            emails = set()
            buyer_email = get_buyer_email(db, t)
            if buyer_email:
                emails.add(buyer_email)

            supplier_ids = (
                db.query(TenderProposal.supplier_id)
                .filter(TenderProposal.tender_id == t.id)
                .distinct()
                .all()
            )
            for (supplier_id,) in supplier_ids:
                supplier = db.query(User).filter(User.id == supplier_id).first()
                if supplier:
                    emails.add(supplier.email)

            if emails:
                notify_deadline_reminder.delay(t.id, t.title, days, sorted(emails))
                sent += 1
        return {"reminders_sent": sent}
    finally:
        db.close()


@celery_app.task
def send_tender_closure_report(tender_id: int) -> dict:
    from app.models.proposal import TenderProposal
    from app.models.tender import TenderStatus
    from app.services.notifications import get_buyer_email, queue_tender_closed

    db = SessionLocal()
    try:
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if not tender:
            return {"status": "not_found"}

        proposals = (
            db.query(TenderProposal)
            .filter(TenderProposal.tender_id == tender_id)
            .order_by(TenderProposal.score.desc())
            .all()
        )
        content = _build_tender_closure_pdf(tender, proposals)
        filename = f"tender_{tender_id}_closure.pdf"
        file_url = save_report_file(filename, content)

        buyer_email = get_buyer_email(db, tender)
        if buyer_email:
            queue_tender_closed(db, tender, file_url)

        return {"status": "queued", "file_url": file_url, "buyer_email": buyer_email}
    finally:
        db.close()


def _build_tender_closure_pdf(tender, proposals: list) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(50, 800, f"SmartTender — Тендер #{tender.id} есебі")
    c.drawString(50, 780, f"Атауы: {tender.title}")
    c.drawString(50, 760, f"Статус: {tender.status.value}")
    c.drawString(50, 740, f"Бюджет: {tender.budget}")
    y = 710
    c.drawString(50, y, "Ұсыныстар:")
    y -= 20
    for p in proposals[:20]:
        c.drawString(
            50,
            y,
            f"#{p.supplier_id} — {p.price} ₸ — {p.delivery_days} күн — балл {p.score}",
        )
        y -= 18
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    buffer.seek(0)
    return buffer.read()


def _build_pdf_bytes(period: str, tenders: list) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(50, 800, f"SmartTender — Айлық есеп {period}")
    y = 770
    for t in tenders[:30]:
        c.drawString(50, y, f"#{t.id} {t.title} — {t.status.value} — {t.budget}")
        y -= 20
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    buffer.seek(0)
    return buffer.read()


def _build_excel_bytes(ratings: list) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Supplier Ratings"
    ws.append(["supplier_id", "tender_id", "quality", "delivery", "avg"])
    for r in ratings:
        ws.append([r.supplier_id, r.tender_id, float(r.quality_score), float(r.delivery_score), float(r.avg_score)])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


@celery_app.task(bind=True)
def generate_budget_analytics(self, period: str, user_id: int | None = None) -> dict:
    from datetime import UTC, timedelta
    from app.models.department import Department
    from app.models.category import Category

    db = SessionLocal()
    try:
        year, month = period.split("-") if "-" in period else (period[:4], period[5:7])
        start_date = datetime(int(year), int(month), 1, tzinfo=UTC)
        if int(month) == 12:
            end_date = datetime(int(year) + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
        else:
            end_date = datetime(int(year), int(month) + 1, 1, tzinfo=UTC) - timedelta(seconds=1)

        tenders = db.query(Tender).filter(
            Tender.created_at >= start_date,
            Tender.created_at <= end_date
        ).all()

        analytics_data = {
            "period": period,
            "total_budget": sum(float(t.budget) for t in tenders),
            "total_tenders": len(tenders),
            "by_department": {},
            "by_category": {},
            "by_status": {}
        }

        for t in tenders:
            dept = db.query(Department).filter(Department.id == t.created_by).first()
            dept_name = dept.name if dept else "Unknown"
            analytics_data["by_department"][dept_name] = analytics_data["by_department"].get(dept_name, 0) + float(t.budget)

            cat = t.category
            cat_name = cat.name if cat else "Uncategorized"
            analytics_data["by_category"][cat_name] = analytics_data["by_category"].get(cat_name, 0) + float(t.budget)

            status = t.status.value
            analytics_data["by_status"][status] = analytics_data["by_status"].get(status, 0) + 1

        content = _build_budget_analytics_bytes(analytics_data)
        filename = f"budget_analytics_{period}.xlsx"
        file_url = save_report_file(filename, content)

        report = Report(
            report_type=ReportType.BUDGET_ANALYTICS,
            period=period,
            file_url=file_url,
            generated_by=user_id,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report_id": report.id, "file_url": file_url}
    finally:
        db.close()


def _build_budget_analytics_bytes(data: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Analytics"

    ws.append(["SmartTender — Бюджет аналитикасы"])
    ws.append(["Период:", data["period"]])
    ws.append([])
    
    ws.append(["Жалпы бюджет:", data["total_budget"]])
    ws.append(["Тендер саны:", data["total_tenders"]])
    ws.append([])

    ws.append(["Бөлім бойынша"])
    ws.append(["Бөлім", "Бюджет"])
    for dept, budget in data["by_department"].items():
        ws.append([dept, budget])
    ws.append([])

    ws.append(["Санат бойынша"])
    ws.append(["Санат", "Бюджет"])
    for cat, budget in data["by_category"].items():
        ws.append([cat, budget])
    ws.append([])

    ws.append(["Статус бойынша"])
    ws.append(["Статус", "Саны"])
    for status, count in data["by_status"].items():
        ws.append([status, count])

    for row in ws.iter_rows(min_row=1, max_row=3):
        for cell in row:
            cell.font = Font(bold=True)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
