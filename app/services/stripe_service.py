"""
Stripe payment service for SmartTender deposit system.

Business rules:
  - Deposit = 1% of tender budget, minimum $10
  - Deposit held until tender CLOSED
  - Successful completion → deposit returned (refunded)
  - Buyer cancels after proposals received → deposit kept (platform penalty)
"""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.payment import Payment, PaymentStatus
from app.models.tender import Tender, TenderStatus

logger = logging.getLogger(__name__)
settings = get_settings()

MIN_DEPOSIT_CENTS = 1000   # $10.00 minimum
DEPOSIT_PERCENT = 0.01     # 1%


def calculate_deposit_cents(budget: Decimal) -> int:
    """
    Calculate deposit amount in cents.
    deposit = max(budget * 1%, $10) — in USD cents.
    """
    deposit_usd = float(budget) * DEPOSIT_PERCENT
    deposit_cents = max(int(deposit_usd * 100), MIN_DEPOSIT_CENTS)
    return deposit_cents


def create_payment_intent(
    db: Session,
    tender_id: int,
    buyer_id: int,
    currency: str = "usd",
) -> Payment:
    """
    Create a Stripe PaymentIntent and record it in the database.

    Returns the Payment DB record with client_secret stored in a transient attribute.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise ValueError(f"Tender {tender_id} not found")

    if tender.created_by != buyer_id:
        raise PermissionError("Only the tender creator can pay the deposit")

    amount_cents = calculate_deposit_cents(tender.budget)

    # Check if there's already a pending/succeeded payment
    existing = (
        db.query(Payment)
        .filter(
            Payment.tender_id == tender_id,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.SUCCEEDED]),
        )
        .first()
    )
    if existing:
        raise ValueError("Payment already exists for this tender")

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata={
                "tender_id": str(tender_id),
                "buyer_id": str(buyer_id),
                "tender_title": tender.title[:500],
            },
            description=f"SmartTender deposit for tender #{tender_id}: {tender.title}",
        )

        payment = Payment(
            tender_id=tender_id,
            buyer_id=buyer_id,
            amount=Decimal(str(amount_cents / 100)),  # store in dollars
            currency=currency,
            stripe_payment_intent_id=intent["id"],
            status=PaymentStatus.PENDING,
        )
        db.add(payment)

        # Move tender to PAYMENT_PENDING
        tender.status = TenderStatus.PAYMENT_PENDING
        db.commit()
        db.refresh(payment)

        # Attach client_secret as a transient attribute for API response
        payment._client_secret = intent["client_secret"]  # type: ignore[attr-defined]
        return payment

    except Exception as exc:
        db.rollback()
        logger.error("Stripe PaymentIntent creation failed: %s", exc)
        raise


def handle_payment_succeeded(db: Session, payment_intent_id: str) -> None:
    """
    Called when Stripe fires payment_intent.succeeded.
    Marks tender as PUBLISHED and payment as SUCCEEDED.
    """
    payment = db.query(Payment).filter(
        Payment.stripe_payment_intent_id == payment_intent_id
    ).first()

    if not payment:
        logger.warning("Payment not found for intent %s", payment_intent_id)
        return

    payment.status = PaymentStatus.SUCCEEDED

    tender = db.query(Tender).filter(Tender.id == payment.tender_id).first()
    if tender and tender.status == TenderStatus.PAYMENT_PENDING:
        tender.status = TenderStatus.PUBLISHED
        # Notify suppliers
        try:
            from app.tasks.notification_tasks import notify_tender_published
            from app.database import SessionLocal
            from app.models.user import User, UserRole
            db2 = SessionLocal()
            try:
                suppliers = db2.query(User).filter(
                    User.role == UserRole.SUPPLIER, User.is_active.is_(True)
                ).all()
                emails = [u.email for u in suppliers if u.is_verified]
            finally:
                db2.close()
            notify_tender_published.delay(tender.id, tender.title, float(tender.budget), emails)
        except Exception as exc:
            logger.warning("Could not queue tender published notification: %s", exc)

    db.commit()
    logger.info("Payment succeeded: intent=%s, tender=%d", payment_intent_id, payment.tender_id)


def handle_payment_failed(db: Session, payment_intent_id: str) -> None:
    """
    Called when Stripe fires payment_intent.payment_failed.
    Reverts tender to DRAFT, notifies buyer.
    """
    payment = db.query(Payment).filter(
        Payment.stripe_payment_intent_id == payment_intent_id
    ).first()

    if not payment:
        logger.warning("Payment not found for intent %s", payment_intent_id)
        return

    payment.status = PaymentStatus.FAILED

    tender = db.query(Tender).filter(Tender.id == payment.tender_id).first()
    if tender and tender.status == TenderStatus.PAYMENT_PENDING:
        tender.status = TenderStatus.DRAFT

    db.commit()

    # Notify buyer
    try:
        from app.database import SessionLocal
        from app.models.user import User
        from app.tasks.notification_tasks import send_telegram_message
        from app.tasks.email_tasks import send_email_notification

        db2 = SessionLocal()
        try:
            buyer = db2.query(User).filter(User.id == payment.buyer_id).first()
            if buyer:
                send_email_notification.delay(
                    buyer.email,
                    f"Төлем сәтсіз: {tender.title if tender else payment.tender_id}",
                    "Тендер депозитін төлеу сәтсіз аяқталды. Қайта байқап көріңіз.",
                )
                if buyer.telegram_chat_id:
                    send_telegram_message.delay(
                        buyer.telegram_chat_id,
                        "❌ <b>Төлем сәтсіз!</b>\n\nТендер депозитін төлеу сәтсіз аяқталды. Платформада қайта байқап көріңіз.",
                    )
        finally:
            db2.close()
    except Exception as exc:
        logger.warning("Could not notify buyer about payment failure: %s", exc)

    logger.info("Payment failed: intent=%s", payment_intent_id)


def handle_charge_refunded(db: Session, payment_intent_id: str | None) -> None:
    """
    Called when Stripe fires charge.refunded.
    Marks payment as REFUNDED.
    """
    if not payment_intent_id:
        return

    payment = db.query(Payment).filter(
        Payment.stripe_payment_intent_id == payment_intent_id
    ).first()

    if not payment:
        logger.warning("No payment found for refund intent %s", payment_intent_id)
        return

    payment.status = PaymentStatus.REFUNDED
    db.commit()
    logger.info("Payment refunded: intent=%s, tender=%d", payment_intent_id, payment.tender_id)
