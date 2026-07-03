from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, selectinload

from app.core.cache import (
    TTL_TENDERS_ACTIVE,
    cache_get,
    cache_key_tenders_active,
    cache_set,
    invalidate_tenders_cache,
)
from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.database import get_db
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.models.proposal import TenderProposal
from app.schemas.tender import TenderCreate, TenderResponse, TenderStatusUpdate, TenderUpdate
from app.services.notifications import (
    queue_tender_awarded,
    queue_tender_closed,
    queue_tender_published,
    tender_requires_approval,
)

router = APIRouter()


def _tender_to_dict(tender: Tender) -> dict:
    return TenderResponse.model_validate(tender).model_dump()


@router.post("", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
async def create_tender(
    tender_data: TenderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    allowed = {
        UserRole.EMPLOYEE,
        UserRole.BUYER,
        UserRole.SUPERADMIN,
    }
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tenders",
        )

    new_tender = Tender(**tender_data.model_dump(), created_by=current_user.id)
    db.add(new_tender)
    db.commit()
    db.refresh(new_tender)
    invalidate_tenders_cache()
    return new_tender


@router.get("", response_model=list[TenderResponse])
async def get_tenders(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    cache_key = cache_key_tenders_active(page, status_filter)

    cached = cache_get(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    query = db.query(Tender).options(
        selectinload(Tender.category),
        selectinload(Tender.creator),
    )

    if status_filter:
        try:
            status_enum = TenderStatus(status_filter.lower())
            query = query.filter(Tender.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    tenders = (
        query.order_by(Tender.deadline.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    data = [_tender_to_dict(t) for t in tenders]
    cache_set(cache_key, data, TTL_TENDERS_ACTIVE)
    response.headers["X-Cache"] = "MISS"
    return data


@router.get("/{tender_id}", response_model=TenderResponse)
async def get_tender(tender_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload

    tender = (
        db.query(Tender)
        .options(
            selectinload(Tender.category),
            selectinload(Tender.creator),
            selectinload(Tender.proposals).joinedload(TenderProposal.supplier)
        )
        .filter(Tender.id == tender_id)
        .first()
    )

    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    return tender


@router.patch("/{tender_id}", response_model=TenderResponse)
async def update_tender(
    tender_id: int,
    tender_data: TenderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()

    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    if tender.created_by != current_user.id and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tender",
        )

    for field, value in tender_data.model_dump(exclude_unset=True).items():
        setattr(tender, field, value)

    db.commit()
    db.refresh(tender)
    invalidate_tenders_cache()
    return tender


@router.patch("/{tender_id}/status", response_model=TenderResponse)
async def update_tender_status(
    tender_id: int,
    status_data: TenderStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()

    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    if status_data.status == TenderStatus.PUBLISHED and (
        tender_requires_approval(db, tender)
        and tender.approval_status != "approved"
        and current_user.role != UserRole.SUPERADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender must complete approval workflow before publishing",
        )

    old_status = tender.status
    tender.status = status_data.status

    if status_data.status == TenderStatus.PUBLISHED and old_status != TenderStatus.PUBLISHED:
        queue_tender_published(db, tender.id, tender.title)
        # Telegram: notify all suppliers
        from app.tasks.notification_tasks import notify_tender_published as tg_notify_published
        from app.services.notifications import get_supplier_users
        suppliers = get_supplier_users(db)
        supplier_emails = [u.email for u in suppliers if u.is_verified]
        tg_notify_published.delay(tender.id, tender.title, float(tender.budget), supplier_emails)

    if status_data.status == TenderStatus.AWARDED and old_status != TenderStatus.AWARDED:
        queue_tender_awarded(db, tender.id, tender.title)

    if status_data.status == TenderStatus.CLOSED and old_status != TenderStatus.CLOSED:
        from app.tasks.report_tasks import send_tender_closure_report

        send_tender_closure_report.delay(tender.id)

    db.commit()
    db.refresh(tender)
    invalidate_tenders_cache()
    return tender


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(
    tender_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()

    if not tender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found")

    if tender.created_by != current_user.id and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this tender",
        )

    db.delete(tender)
    db.commit()
    invalidate_tenders_cache()
    return None
