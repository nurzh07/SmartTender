from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.proposal import ProposalStatus, TenderProposal
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.schemas.proposal import ProposalCreate, ProposalResponse
from app.services.scoring import calculate_proposal_score, get_supplier_avg_rating, recalculate_tender_scores
from app.services.storage import save_proposal_file

router = APIRouter()


@router.post(
    "/{tender_id}/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal(
    tender_id: int,
    proposal_data: ProposalCreate,
    current_user: User = Depends(require_roles(UserRole.SUPPLIER)),
    db: Session = Depends(get_db),
):
    return _create_proposal(db, tender_id, current_user, proposal_data, file_url=None)


@router.post(
    "/{tender_id}/proposals/upload",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal_with_file(
    tender_id: int,
    price: Decimal = Form(...),
    delivery_days: int = Form(...),
    comment: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.SUPPLIER)),
    db: Session = Depends(get_db),
):
    content = await file.read()
    file_url = save_proposal_file(tender_id, current_user.id, file.filename or "proposal.pdf", content)
    data = ProposalCreate(price=price, delivery_days=delivery_days, comment=comment, file_url=file_url)
    return _create_proposal(db, tender_id, current_user, data, file_url=file_url)


def _create_proposal(
    db: Session,
    tender_id: int,
    current_user: User,
    proposal_data: ProposalCreate,
    file_url: str | None,
) -> TenderProposal:
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

    avg_rating = get_supplier_avg_rating(db, current_user.id)
    score = calculate_proposal_score(
        proposal_data.price, proposal_data.delivery_days, tender.budget, avg_rating
    )
    proposal = TenderProposal(
        tender_id=tender_id,
        supplier_id=current_user.id,
        score=score,
        file_url=file_url or proposal_data.file_url,
        price=proposal_data.price,
        delivery_days=proposal_data.delivery_days,
        comment=proposal_data.comment,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    recalculate_tender_scores(db, tender_id)
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
