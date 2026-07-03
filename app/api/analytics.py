"""
Analytics API endpoints with Redis caching (1-hour TTL).

Endpoints:
  GET /analytics/buyer/dashboard
  GET /analytics/supplier/dashboard
  GET /analytics/admin/dashboard
  GET /analytics/tenders/monthly?year={year}
  GET /analytics/suppliers/top10
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.core.rbac import require_roles
from app.core.redis_client import redis_client
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AdminDashboard,
    BuyerDashboard,
    MonthlyBar,
    SupplierDashboard,
    TopSupplier,
)
from app.services.analytics_service import (
    get_admin_dashboard,
    get_buyer_dashboard,
    get_monthly_tenders,
    get_supplier_dashboard,
    _top_suppliers,
)

router = APIRouter()
logger = logging.getLogger(__name__)

ANALYTICS_TTL = 3600  # 1 hour


def _analytics_cache_key(role: str, user_id: int | str) -> str:
    month = datetime.utcnow().strftime("%Y-%m")
    return f"analytics:{role}:{user_id}:{month}"


def _cache_get(key: str):
    try:
        raw = redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key: str, data) -> None:
    try:
        redis_client.setex(key, ANALYTICS_TTL, json.dumps(data, default=str))
    except Exception as exc:
        logger.warning("Analytics cache set error: %s", exc)


# ──────────────────────────────────────────────────────────────
# BUYER dashboard
# ──────────────────────────────────────────────────────────────

@router.get(
    "/buyer/dashboard",
    response_model=BuyerDashboard,
    summary="Buyer analytics dashboard",
    tags=["analytics"],
)
async def buyer_dashboard(
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    """
    Returns analytics dashboard data for buyers.

    Cached in Redis for 1 hour. Key: analytics:buyer:{user_id}:{month}
    """
    cache_key = _analytics_cache_key("buyer", current_user.id)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = get_buyer_dashboard(db, current_user.id)
    _cache_set(cache_key, data.model_dump())
    return data


# ──────────────────────────────────────────────────────────────
# SUPPLIER dashboard
# ──────────────────────────────────────────────────────────────

@router.get(
    "/supplier/dashboard",
    response_model=SupplierDashboard,
    summary="Supplier analytics dashboard",
    tags=["analytics"],
)
async def supplier_dashboard(
    current_user: User = Depends(require_roles(UserRole.SUPPLIER, UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    """
    Returns analytics dashboard data for suppliers.

    Cached in Redis for 1 hour.
    """
    cache_key = _analytics_cache_key("supplier", current_user.id)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = get_supplier_dashboard(db, current_user.id)
    _cache_set(cache_key, data.model_dump())
    return data


# ──────────────────────────────────────────────────────────────
# ADMIN dashboard
# ──────────────────────────────────────────────────────────────

@router.get(
    "/admin/dashboard",
    response_model=AdminDashboard,
    summary="Superadmin analytics dashboard",
    tags=["analytics"],
)
async def admin_dashboard(
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    """
    Platform-wide analytics for superadmins.

    Cached in Redis for 1 hour.
    """
    cache_key = _analytics_cache_key("admin", "global")
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = get_admin_dashboard(db)
    _cache_set(cache_key, data.model_dump())
    return data


# ──────────────────────────────────────────────────────────────
# Monthly tenders
# ──────────────────────────────────────────────────────────────

@router.get(
    "/tenders/monthly",
    response_model=list[MonthlyBar],
    summary="Monthly tender activity for a given year",
    tags=["analytics"],
)
async def monthly_tenders(
    year: int = Query(default=datetime.utcnow().year, ge=2020, le=2030),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Returns month-by-month tender counts for the given year."""
    cache_key = f"analytics:tenders:monthly:{year}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = get_monthly_tenders(db, year)
    _cache_set(cache_key, [d.model_dump() for d in data])
    return data


# ──────────────────────────────────────────────────────────────
# Top suppliers
# ──────────────────────────────────────────────────────────────

@router.get(
    "/suppliers/top10",
    response_model=list[TopSupplier],
    summary="Top 10 suppliers by win rate",
    tags=["analytics"],
)
async def top_suppliers(
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
    db: Session = Depends(get_db),
):
    """Returns top 10 suppliers by win rate across platform."""
    cache_key = _analytics_cache_key("top_suppliers", "global")
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _top_suppliers(db, limit=10)
    _cache_set(cache_key, [d.model_dump() for d in data])
    return data
