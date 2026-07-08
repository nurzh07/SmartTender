from pydantic import BaseModel
from datetime import datetime
from app.models.report import ReportType, ReportStatus


class ReportBase(BaseModel):
    title: str
    type: ReportType


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    id: int
    status: ReportStatus
    file_path: str | None
    file_type: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
