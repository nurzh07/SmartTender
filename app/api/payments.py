"""
Payments API.

POST /payments/create-intent  – create Stripe PaymentIntent for tender deposit
GET  /payments/tender/{id}    – get payment status for a tender
GET  /payments/config         – return Stripe publishable key (frontend needs this)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.payment import Payment
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentStatusResponse,
)
from app.services.stripe_service import (
    calculate_deposit_cents,
    create_payment_intent,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/config",
    summary="Get Stripe publishable key",
    tags=["payments"],
)
async def get_stripe_config(
    current_user: User = Depends(get_current_active_user),
):
    """Returns Stripe publishable key for Stripe.js initialization."""
    from app.config import get_settings
    s = get_settings()
    return {
        "publishable_key": s.STRIPE_PUBLISHABLE_KEY,
        "enabled": bool(s.STRIPE_SECRET_KEY),
    }


@router.post(
    "/create-intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe PaymentIntent for tender deposit",
    tags=["payments"],
)
async def create_intent(
    body: PaymentIntentCreate,
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe PaymentIntent for the tender deposit.

    Deposit = 1% of tender budget, minimum $10.
    Returns the `client_secret` to use with Stripe.js on the frontend.
    The tender status changes to `payment_pending` after calling this endpoint.
    """
    tender = db.query(Tender).filter(Tender.id == body.tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if tender.created_by != current_user.id and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the tender creator can initiate payment",
        )

    try:
        payment = create_payment_intent(
            db=db,
            tender_id=body.tender_id,
            buyer_id=current_user.id,
            currency=body.currency,
        )

        client_secret = getattr(payment, "_client_secret", "")
        amount_cents = calculate_deposit_cents(tender.budget)

        return PaymentIntentResponse(
            payment_id=payment.id,
            tender_id=payment.tender_id,
            client_secret=client_secret,
            payment_intent_id=payment.stripe_payment_intent_id or "",
            amount=amount_cents / 100,
            currency=payment.currency,
            status=payment.status.value,
        )

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        logger.error("Payment intent creation error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Stripe payment service unavailable. Please try again.",
        )


@router.get(
    "/tender/{tender_id}",
    response_model=PaymentStatusResponse,
    summary="Get payment status for a tender",
    tags=["payments"],
)
async def get_payment_status(
    tender_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the latest payment record for a given tender."""
    payment = (
        db.query(Payment)
        .filter(Payment.tender_id == tender_id)
        .order_by(Payment.created_at.desc())
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="No payment found for this tender")

    # Only buyer/superadmin can see payment details
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if (
        tender
        and tender.created_by != current_user.id
        and current_user.role != UserRole.SUPERADMIN
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    return PaymentStatusResponse(
        payment_id=payment.id,
        tender_id=payment.tender_id,
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status.value,
        stripe_payment_intent_id=payment.stripe_payment_intent_id,
        created_at=payment.created_at,
    )
