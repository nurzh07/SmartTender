from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import db_transaction
from app.models.approval import ApprovalStatus, ApprovalWorkflow
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole

STEP_DEPARTMENT_HEAD = 1


def init_approval_workflow(db: Session, tender: Tender) -> list[ApprovalWorkflow]:
    existing = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.tender_id == tender.id).count()
    if existing:
        return db.query(ApprovalWorkflow).filter(ApprovalWorkflow.tender_id == tender.id).all()

    steps = [
        ApprovalWorkflow(tender_id=tender.id, step=STEP_DEPARTMENT_HEAD, status=ApprovalStatus.PENDING),
    ]
    with db_transaction(db):
        db.add_all(steps)
        tender.approval_status = "pending_approval"
    return steps


def get_current_pending_step(db: Session, tender_id: int) -> ApprovalWorkflow | None:
    return (
        db.query(ApprovalWorkflow)
        .filter(
            ApprovalWorkflow.tender_id == tender_id,
            ApprovalWorkflow.status == ApprovalStatus.PENDING,
        )
        .order_by(ApprovalWorkflow.step.asc())
        .first()
    )


def required_role_for_step(step: int) -> UserRole:
    if step == STEP_DEPARTMENT_HEAD:
        return UserRole.DEPARTMENT_HEAD
    raise ValueError(f"Unsupported approval step: {step}")


def process_approval(
    db: Session,
    tender: Tender,
    approver: User,
    approved: bool,
    comment: str | None,
) -> ApprovalWorkflow:
    current = get_current_pending_step(db, tender.id)
    if not current:
        raise ValueError("No pending approval step")

    expected_role = required_role_for_step(current.step)
    if approver.role not in (expected_role, UserRole.SUPERADMIN):
        raise PermissionError(f"Requires role {expected_role.value}")

    with db_transaction(db):
        if approved:
            current.status = ApprovalStatus.APPROVED
            current.approver_id = approver.id
            current.comment = comment
            current.approved_at = datetime.now(UTC)

            next_step = get_current_pending_step(db, tender.id)
            if not next_step:
                tender.approval_status = "approved"
            else:
                tender.approval_status = f"pending_step_{next_step.step}"
        else:
            current.status = ApprovalStatus.REJECTED
            current.approver_id = approver.id
            current.comment = comment
            current.approved_at = datetime.now(UTC)
            tender.approval_status = "rejected"
            tender.status = TenderStatus.DRAFT

    db.refresh(current)
    return current
