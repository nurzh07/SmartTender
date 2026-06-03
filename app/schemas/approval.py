from datetime import datetime

from pydantic import BaseModel

from app.models.approval import ApprovalStatus


class ApprovalAction(BaseModel):
    comment: str | None = None


class ApprovalStepResponse(BaseModel):
    id: int
    tender_id: int
    step: int
    status: ApprovalStatus
    comment: str | None
    approver_id: int | None
    approved_at: datetime | None

    class Config:
        from_attributes = True
