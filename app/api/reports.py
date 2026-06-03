from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.report import Report, ReportType
from app.models.user import User, UserRole
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.tasks.report_tasks import generate_monthly_pdf_report, generate_supplier_ratings_excel

router = APIRouter()
settings = get_settings()


@router.post("/generate", response_model=dict)
async def generate_report(
    body: ReportGenerateRequest,
    current_user: User = Depends(
        require_roles(UserRole.PROCUREMENT_MANAGER, UserRole.SUPERADMIN)
    ),
    db: Session = Depends(get_db),
):
    from app.tasks.report_tasks import generate_budget_analytics
    
    if body.report_type == ReportType.MONTHLY_TENDERS_PDF:
        task = generate_monthly_pdf_report.delay(body.period, current_user.id)
    elif body.report_type == ReportType.SUPPLIER_RATINGS_EXCEL:
        task = generate_supplier_ratings_excel.delay(body.period, current_user.id)
    elif body.report_type == ReportType.BUDGET_ANALYTICS:
        task = generate_budget_analytics.delay(body.period, current_user.id)
    else:
        task = generate_monthly_pdf_report.delay(body.period, current_user.id)
    return {"task_id": task.id, "status": "queued", "report_type": body.report_type.value}


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(Report).order_by(Report.created_at.desc()).limit(20).all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.file_url:
        raise HTTPException(status_code=404, detail="Report file not found")

    if report.file_url.startswith("/api/reports/files/"):
        filename = report.file_url.split("/")[-1]
        path = Path(settings.UPLOAD_DIR) / "reports" / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail="File missing on disk")
        return FileResponse(path, filename=filename)

    raise HTTPException(status_code=400, detail="File stored externally; use file_url")


@router.get("/files/{filename}")
async def serve_report_file(filename: str):
    path = Path(settings.UPLOAD_DIR) / "reports" / filename.replace("..", "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)
