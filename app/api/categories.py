from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.cache import (
    TTL_CATEGORIES,
    cache_get,
    cache_key_categories,
    cache_set,
    invalidate_tenders_cache,
)
from app.core.rbac import require_roles
from app.database import get_db
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
async def list_categories(response: Response, db: Session = Depends(get_db)):
    cache_key = cache_key_categories()
    cached = cache_get(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    categories = db.query(Category).order_by(Category.name).all()
    data = [CategoryResponse.model_validate(c).model_dump() for c in categories]
    cache_set(cache_key, data, TTL_CATEGORIES)
    response.headers["X-Cache"] = "MISS"
    return data


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(UserRole.SUPERADMIN, UserRole.BUYER)
    ),
):
    existing = db.query(Category).filter(Category.name == category_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already exists",
        )

    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    from app.core.cache import cache_delete

    cache_delete(cache_key_categories())
    invalidate_tenders_cache()
    return category
