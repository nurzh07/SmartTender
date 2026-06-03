from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.cache import TTL_SUPPLIER_RATING, cache_get, cache_key_supplier_rating, cache_set
from app.database import get_db
from app.models.supplier_rating import SupplierRating
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_suppliers(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == UserRole.SUPPLIER, User.is_active.is_(True)).all()


@router.get("/{supplier_id}/rating")
async def get_supplier_rating(
    supplier_id: int,
    response: Response,
    db: Session = Depends(get_db),
):
    cache_key = cache_key_supplier_rating(supplier_id)
    cached = cache_get(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    user = db.query(User).filter(User.id == supplier_id, User.role == UserRole.SUPPLIER).first()
    if not user:
        raise HTTPException(status_code=404, detail="Supplier not found")

    ratings = db.query(SupplierRating).filter(SupplierRating.supplier_id == supplier_id).all()
    if not ratings:
        data = {"supplier_id": supplier_id, "avg_score": None, "ratings_count": 0}
    else:
        avg = sum(float(r.avg_score) for r in ratings) / len(ratings)
        data = {
            "supplier_id": supplier_id,
            "avg_score": round(avg, 2),
            "ratings_count": len(ratings),
            "details": [
                {
                    "tender_id": r.tender_id,
                    "quality_score": float(r.quality_score),
                    "delivery_score": float(r.delivery_score),
                    "avg_score": float(r.avg_score),
                }
                for r in ratings
            ],
        }

    cache_set(cache_key, data, TTL_SUPPLIER_RATING)
    response.headers["X-Cache"] = "MISS"
    return data
