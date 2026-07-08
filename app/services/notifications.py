from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationType
from app.models.proposal import TenderProposal
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.services.email_utils import (
    send_tender_published_email as send_tender_published_email_resend,
    send_new_proposal_email as send_new_proposal_email_resend,
    send_winner_selected_email as send_winner_selected_email_resend,
    send_tender_closed_email as send_tender_closed_email_resend
)


def create_in_app_notification(
    db: Session,
    user_id: int,
    ntype: NotificationType,
    message: str,
    channel: NotificationChannel = NotificationChannel.IN_APP,
) -> Notification:
    n = Notification(user_id=user_id, type=ntype, message=message, channel=channel)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_supplier_users(db: Session) -> list[User]:
    return db.query(User).filter(User.role == UserRole.SUPPLIER, User.is_active.is_(True)).all()


def get_buyer_email(db: Session, tender: Tender) -> str | None:
    creator = db.query(User).filter(User.id == tender.created_by).first()
    if creator:
        return creator.email
    buyer = (
        db.query(User)
        .filter(User.role == UserRole.BUYER, User.is_active.is_(True))
        .order_by(User.id.asc())
        .first()
    )
    return buyer.email if buyer else None


def tender_requires_approval(db: Session, tender: Tender) -> bool:
    creator = db.query(User).filter(User.id == tender.created_by).first()
    return creator is not None and creator.role == UserRole.EMPLOYEE


def queue_tender_published(db: Session, tender_id: int, title: str) -> None:
    from app.tasks.email_tasks import send_tender_published_email

    suppliers = get_supplier_users(db)
    emails = [u.email for u in suppliers if u.is_verified]
    send_tender_published_email.delay(emails, title, tender_id)
    
    # Send with Resend
    for email in emails:
        send_tender_published_email_resend(email, title, tender_id)


def queue_proposal_received(
    db: Session, tender: Tender, supplier: User, price: str
) -> None:
    from app.tasks.email_tasks import send_new_proposal_email

    buyer_email = get_buyer_email(db, tender)
    if not buyer_email:
        return
    supplier_name = supplier.full_name or supplier.email
    send_new_proposal_email.delay(buyer_email, tender.title, supplier_name)
    
    # Send with Resend
    send_new_proposal_email_resend(buyer_email, tender.title, supplier_name)


def queue_approval_result(db: Session, user_id: int, approved: bool, tender_title: str) -> None:
    from app.tasks.email_tasks import send_email_notification

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    subject = f"SmartTender — Бекіту нәтижесі: {tender_title}"
    message = f"Тендер бекітілді: {'Қабылданды' if approved else 'Қабылданбады'}\nТендер: {tender_title}"
    send_email_notification.delay(user.email, subject, message)
    
    # Note: Approval result email is simple, we can add Resend version later if needed


def queue_tender_awarded(db: Session, tender_id: int, title: str) -> None:
    from app.tasks.email_tasks import send_winner_selected_email

    proposals = (
        db.query(TenderProposal)
        .options()
        .filter(TenderProposal.tender_id == tender_id)
        .order_by(TenderProposal.score.desc())
        .all()
    )
    if not proposals:
        return

    winner = proposals[0]
    winner_user = db.query(User).filter(User.id == winner.supplier_id).first()
    if not winner_user:
        return

    loser_emails = []
    for proposal in proposals[1:]:
        supplier = db.query(User).filter(User.id == proposal.supplier_id).first()
        if supplier and supplier.email != winner_user.email:
            loser_emails.append(supplier.email)

    send_winner_selected_email.delay(winner_user.email, title, loser_emails)
    
    # Send with Resend
    send_winner_selected_email_resend(winner_user.email, title, True)
    for email in loser_emails:
        send_winner_selected_email_resend(email, title, False)


def queue_tender_closed(db: Session, tender: Tender, report_url: str) -> None:
    from app.tasks.email_tasks import send_tender_closed_email

    buyer_email = get_buyer_email(db, tender)
    if not buyer_email:
        return
    send_tender_closed_email.delay(buyer_email, tender.title, report_url)
    
    # Send with Resend
    send_tender_closed_email_resend(buyer_email, tender.title, report_url)
