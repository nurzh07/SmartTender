from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class PaymentIntentCreate(BaseModel):
    tender_id: int
    currency: str = "usd"


class PaymentIntentResponse(BaseModel):
    payment_id: int
    tender_id: int
    client_secret: str
    payment_intent_id: str
    amount: float          # in dollars (not cents)
    currency: str
    status: str


class PaymentStatusResponse(BaseModel):
    payment_id: int
    tender_id: int
    amount: float
    currency: str
    status: str
    stripe_payment_intent_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True
