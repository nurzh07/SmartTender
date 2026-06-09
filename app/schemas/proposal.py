from pydantic import BaseModel
from decimal import Decimal
from app.models.proposal import ProposalStatus


class ProposalBase(BaseModel):
    price: Decimal
    delivery_days: int
    file_url: str | None = None
    comment: str | None = None


class ProposalCreate(ProposalBase):
    pass


class ProposalResponse(ProposalBase):
    id: int
    tender_id: int
    supplier_id: int
    supplier_name: str | None = None
    score: int
    status: ProposalStatus

    class Config:
        from_attributes = True
