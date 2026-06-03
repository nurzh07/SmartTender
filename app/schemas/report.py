from datetime import datetime

from pydantic import BaseModel

from app.models.report import ReportType


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    period: str


class ReportResponse(BaseModel):
    id: int
    report_type: ReportType
    period: str
    file_url: str | None
    generated_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True
