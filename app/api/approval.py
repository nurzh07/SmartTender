from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.cache import invalidate_tenders_cache
from app.database import get_db
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.schemas.approval import ApprovalAction, ApprovalStepResponse
from app.services.approval_service import init_approval_workflow, process_approval
from app.services.notifications import queue_approval_result

router = APIRouter()


@router.post("/{tender_id}/submit", response_model=list[ApprovalStepResponse])
async def submit_for_approval(
    tender_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models.tender import TenderStatus

    allowed_roles = (UserRole.EMPLOYEE, UserRole.BUYER, UserRole.SUPERADMIN)
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Сіздің рөліңіз бекітуге жіберуге рұқсат етілмеген")

    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер табылмады")
    if tender.created_by != current_user.id and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Бұл сіздің өтініміңіз емес")
    if tender.status != TenderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Тек жоба (draft) статусын бекітуге жіберуге болады")
    approval_state = tender.approval_status or "draft"
    if approval_state in ("pending_approval", "approved") or approval_state.startswith("pending_step_"):
        raise HTTPException(status_code=400, detail="Өтінім бекітуге жіберілген")

    steps = init_approval_workflow(db, tender)
    return steps


@router.post("/{tender_id}/approve", response_model=ApprovalStepResponse)
async def approve_tender(
    tender_id: int,
    data: ApprovalAction,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    try:
        step = process_approval(db, tender, current_user, approved=True, comment=data.comment)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    creator = db.query(User).filter(User.id == tender.created_by).first()
    if creator:
        queue_approval_result(db, creator.id, True, tender.title)

    if tender.approval_status == "approved":
        invalidate_tenders_cache()

    return step


@router.post("/{tender_id}/reject", response_model=ApprovalStepResponse)
async def reject_tender(
    tender_id: int,
    data: ApprovalAction,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    try:
        step = process_approval(db, tender, current_user, approved=False, comment=data.comment)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    creator = db.query(User).filter(User.id == tender.created_by).first()
    if creator:
        queue_approval_result(db, creator.id, False, tender.title)

    return step


@router.get("/{tender_id}/approval", response_model=list[ApprovalStepResponse])
async def get_approval_steps(tender_id: int, db: Session = Depends(get_db)):
    from app.models.approval import ApprovalWorkflow

    steps = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.tender_id == tender_id)
        .order_by(ApprovalWorkflow.step)
        .all()
    )
    return steps
