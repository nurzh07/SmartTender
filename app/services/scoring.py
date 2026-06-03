from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.proposal import TenderProposal
from app.models.supplier_rating import SupplierRating
from app.models.user import UserRole


def calculate_proposal_score(
    price: Decimal,
    delivery_days: int,
    budget: Decimal,
    supplier_avg_rating: float | None = None,
) -> int:
    if budget <= 0:
        price_score = 50
    else:
        price_ratio = float(min(price / budget, 2.0))
        price_score = max(0, 100 - int(price_ratio * 50))

    delivery_score = max(0, 100 - min(delivery_days, 100))
    rating_bonus = int((supplier_avg_rating or 50) * 0.2)
    return min(100, int(price_score * 0.5 + delivery_score * 0.3 + rating_bonus))


def get_supplier_avg_rating(db: Session, supplier_id: int) -> float | None:
    ratings = db.query(SupplierRating).filter(SupplierRating.supplier_id == supplier_id).all()
    if not ratings:
        return None
    return float(sum(r.avg_score for r in ratings) / len(ratings))


def recalculate_tender_scores(db: Session, tender_id: int) -> None:
    from app.models.tender import Tender

    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        return
    proposals = db.query(TenderProposal).filter(TenderProposal.tender_id == tender_id).all()

    for p in proposals:
        avg = get_supplier_avg_rating(db, p.supplier_id)
        p.score = calculate_proposal_score(p.price, p.delivery_days, tender.budget, avg)
    db.commit()
