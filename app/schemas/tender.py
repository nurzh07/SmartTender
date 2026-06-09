from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.models.tender import TenderStatus


class TenderBase(BaseModel):
    title: str
    description: str | None = None
    budget: Decimal
    deadline: datetime
    category_id: int | None = None


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    budget: Decimal | None = None
    deadline: datetime | None = None
    status: TenderStatus | None = None
    category_id: int | None = None


class TenderResponse(TenderBase):
    id: int
    status: TenderStatus
    created_by: int
    approval_status: str | None = "draft"
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TenderStatusUpdate(BaseModel):
    status: TenderStatus
