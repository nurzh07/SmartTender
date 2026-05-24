from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.proposal import ProposalStatus, TenderProposal
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.schemas.proposal import ProposalCreate, ProposalResponse

router = APIRouter()


def calculate_proposal_score(price: Decimal, delivery_days: int, budget: Decimal) -> int:
    """Simple scoring: lower price and faster delivery = higher score (0-100)."""
    if budget <= 0:
        return 50
    price_ratio = float(min(price / budget, 2.0))
    price_score = max(0, 100 - int(price_ratio * 50))
    delivery_score = max(0, 100 - min(delivery_days, 100))
    return int((price_score * 0.7) + (delivery_score * 0.3))


@router.post(
    "/{tender_id}/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal(
    tender_id: int,
    proposal_data: ProposalCreate,
    current_user: User = Depends(
        require_roles(UserRole.SUPPLIER)
    ),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    if tender.status != TenderStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposals are only accepted for published tenders",
        )

    existing = (
        db.query(TenderProposal)
        .filter(
            TenderProposal.tender_id == tender_id,
            TenderProposal.supplier_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already submitted a proposal for this tender",
        )

    score = calculate_proposal_score(
        proposal_data.price, proposal_data.delivery_days, tender.budget
    )
    proposal = TenderProposal(
        tender_id=tender_id,
        supplier_id=current_user.id,
        score=score,
        **proposal_data.model_dump(),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("/{tender_id}/proposals", response_model=list[ProposalResponse])
async def list_proposals(
    tender_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    query = (
        db.query(TenderProposal)
        .options(selectinload(TenderProposal.supplier))
        .filter(TenderProposal.tender_id == tender_id)
    )

    if current_user.role == UserRole.SUPPLIER:
        query = query.filter(TenderProposal.supplier_id == current_user.id)
    elif current_user.role not in (
        UserRole.SUPERADMIN,
        UserRole.PROCUREMENT_MANAGER,
        UserRole.DEPARTMENT_HEAD,
    ):
        if tender.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view proposals",
            )

    return query.order_by(TenderProposal.score.desc()).all()
