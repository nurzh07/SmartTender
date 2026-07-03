"""
Analytics service — pure DB queries, no caching (caching handled at API layer).
"""

import logging
from datetime import datetime, timedelta, date

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.proposal import TenderProposal, ProposalStatus
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AdminDashboard,
    BuyerDashboard,
    MonthlyBar,
    StatusPie,
    SupplierDashboard,
    TopBuyer,
    TopSupplier,
)

logger = logging.getLogger(__name__)

MONTH_LABELS_KK = {
    1: "Қаңтар", 2: "Ақпан", 3: "Наурыз", 4: "Сәуір",
    5: "Мамыр", 6: "Маусым", 7: "Шілде", 8: "Тамыз",
    9: "Қыркүйек", 10: "Қазан", 11: "Қараша", 12: "Желтоқсан",
}

STATUS_LABEL_KK = {
    "draft": "Жоба",
    "published": "Жарияланды",
    "evaluation": "Бағалауда",
    "awarded": "Жеңімпаз",
    "closed": "Жабылды",
    "payment_pending": "Төлем күтуде",
}


def _last_6_months() -> list[tuple[int, int]]:
    """Returns list of (year, month) for last 6 months including current."""
    today = date.today()
    result = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        result.append((d.year, d.month))
    return result


def _month_key(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


# ═══════════════════════════════════════════════════════════════
# BUYER DASHBOARD
# ═══════════════════════════════════════════════════════════════

def get_buyer_dashboard(db: Session, user_id: int) -> BuyerDashboard:
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    # Base query: only this buyer's tenders
    def buyer_q():
        return db.query(Tender).filter(Tender.created_by == user_id)

    total_this_month = buyer_q().filter(Tender.created_at >= this_month_start).count()
    total_last_month = buyer_q().filter(
        Tender.created_at >= last_month_start,
        Tender.created_at < this_month_start,
    ).count()

    # Budget awarded
    awarded = buyer_q().filter(
        Tender.status.in_([TenderStatus.AWARDED, TenderStatus.CLOSED])
    ).all()
    total_budget_awarded = sum(float(t.budget) for t in awarded)

    # Avg proposals per tender (only buyer's tenders)
    tender_ids = [t.id for t in buyer_q().all()]
    if tender_ids:
        total_proposals = db.query(TenderProposal).filter(
            TenderProposal.tender_id.in_(tender_ids)
        ).count()
        avg_proposals = total_proposals / len(tender_ids) if tender_ids else 0.0
    else:
        avg_proposals = 0.0

    # Status distribution
    status_counts = (
        db.query(Tender.status, func.count(Tender.id))
        .filter(Tender.created_by == user_id)
        .group_by(Tender.status)
        .all()
    )
    status_distribution = [
        StatusPie(
            status=s.value,
            count=c,
            label=STATUS_LABEL_KK.get(s.value, s.value),
        )
        for s, c in status_counts
    ]

    # Monthly activity (last 6 months)
    months = _last_6_months()
    monthly_activity = []
    for year, month in months:
        count = buyer_q().filter(
            extract("year", Tender.created_at) == year,
            extract("month", Tender.created_at) == month,
        ).count()
        monthly_activity.append(MonthlyBar(
            month=_month_key(year, month),
            month_label=f"{MONTH_LABELS_KK[month]} {year}",
            count=count,
        ))

    # Top 5 suppliers by win rate (for this buyer's tenders)
    top_suppliers = _top_suppliers(db, limit=5, buyer_id=user_id)

    return BuyerDashboard(
        total_tenders_this_month=total_this_month,
        total_tenders_last_month=total_last_month,
        total_budget_awarded=total_budget_awarded,
        avg_proposals_per_tender=round(avg_proposals, 2),
        top_suppliers=top_suppliers,
        status_distribution=status_distribution,
        monthly_activity=monthly_activity,
    )


# ═══════════════════════════════════════════════════════════════
# SUPPLIER DASHBOARD
# ═══════════════════════════════════════════════════════════════

def get_supplier_dashboard(db: Session, user_id: int) -> SupplierDashboard:
    proposals = (
        db.query(TenderProposal)
        .filter(TenderProposal.supplier_id == user_id)
        .all()
    )

    total_proposals = len(proposals)
    wins = sum(1 for p in proposals if p.status == ProposalStatus.ACCEPTED)
    win_rate = round((wins / total_proposals * 100) if total_proposals else 0.0, 1)

    # Avg own price
    prices = [float(p.price) for p in proposals]
    avg_own_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    # Market average (all proposals across platform)
    all_prices = db.query(TenderProposal.price).all()
    all_price_vals = [float(r[0]) for r in all_prices if r[0]]
    avg_market_price = round(sum(all_price_vals) / len(all_price_vals), 2) if all_price_vals else 0.0

    # Monthly activity — proposals submitted per month
    months = _last_6_months()
    monthly_activity = []
    for year, month in months:
        count = db.query(TenderProposal).filter(
            TenderProposal.supplier_id == user_id,
            extract("year", TenderProposal.created_at) == year,
            extract("month", TenderProposal.created_at) == month,
        ).count()
        monthly_activity.append(MonthlyBar(
            month=_month_key(year, month),
            month_label=f"{MONTH_LABELS_KK[month]} {year}",
            count=count,
        ))

    # Wins vs losses pie
    losses = total_proposals - wins
    wins_losses = [
        StatusPie(status="won", count=wins, label="Жеңілді"),
        StatusPie(status="lost", count=max(losses, 0), label="Жеңілмеді"),
    ]

    return SupplierDashboard(
        total_proposals=total_proposals,
        win_rate=win_rate,
        avg_own_price=avg_own_price,
        avg_market_price=avg_market_price,
        monthly_activity=monthly_activity,
        wins_losses=wins_losses,
    )


# ═══════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════

def get_admin_dashboard(db: Session) -> AdminDashboard:
    total_users = db.query(User).count()
    total_buyers = db.query(User).filter(User.role == UserRole.BUYER).count()
    total_suppliers = db.query(User).filter(User.role == UserRole.SUPPLIER).count()
    total_tenders = db.query(Tender).count()

    # Transaction volume: sum of awarded/closed tender budgets
    awarded_tenders = db.query(Tender).filter(
        Tender.status.in_([TenderStatus.AWARDED, TenderStatus.CLOSED])
    ).all()
    total_volume = sum(float(t.budget) for t in awarded_tenders)

    # Status distribution
    status_counts = (
        db.query(Tender.status, func.count(Tender.id))
        .group_by(Tender.status)
        .all()
    )
    status_distribution = [
        StatusPie(status=s.value, count=c, label=STATUS_LABEL_KK.get(s.value, s.value))
        for s, c in status_counts
    ]

    # Monthly activity
    months = _last_6_months()
    monthly_activity = []
    for year, month in months:
        count = db.query(Tender).filter(
            extract("year", Tender.created_at) == year,
            extract("month", Tender.created_at) == month,
        ).count()
        budget_sum = sum(
            float(t.budget) for t in db.query(Tender).filter(
                extract("year", Tender.created_at) == year,
                extract("month", Tender.created_at) == month,
            ).all()
        )
        monthly_activity.append(MonthlyBar(
            month=_month_key(year, month),
            month_label=f"{MONTH_LABELS_KK[month]} {year}",
            count=count,
            budget=budget_sum,
        ))

    top_buyers = _top_buyers(db, limit=10)
    top_suppliers = _top_suppliers(db, limit=10)

    return AdminDashboard(
        total_users=total_users,
        total_buyers=total_buyers,
        total_suppliers=total_suppliers,
        total_tenders=total_tenders,
        total_transaction_volume=total_volume,
        status_distribution=status_distribution,
        monthly_activity=monthly_activity,
        top_buyers=top_buyers,
        top_suppliers=top_suppliers,
    )


# ═══════════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════════

def get_monthly_tenders(db: Session, year: int) -> list[MonthlyBar]:
    result = []
    for month in range(1, 13):
        count = db.query(Tender).filter(
            extract("year", Tender.created_at) == year,
            extract("month", Tender.created_at) == month,
        ).count()
        result.append(MonthlyBar(
            month=_month_key(year, month),
            month_label=MONTH_LABELS_KK[month],
            count=count,
        ))
    return result


def _top_suppliers(db: Session, limit: int = 10, buyer_id: int | None = None) -> list[TopSupplier]:
    """Top suppliers by win rate."""
    query = db.query(TenderProposal)
    if buyer_id:
        tender_ids = [
            t.id for t in db.query(Tender).filter(Tender.created_by == buyer_id).all()
        ]
        if not tender_ids:
            return []
        query = query.filter(TenderProposal.tender_id.in_(tender_ids))

    proposals = query.all()

    # Group by supplier
    from collections import defaultdict
    supplier_stats: dict[int, dict] = defaultdict(lambda: {"total": 0, "wins": 0})
    for p in proposals:
        supplier_stats[p.supplier_id]["total"] += 1
        if p.status == ProposalStatus.ACCEPTED:
            supplier_stats[p.supplier_id]["wins"] += 1

    results = []
    for sid, stats in supplier_stats.items():
        user = db.query(User).filter(User.id == sid).first()
        if not user:
            continue
        total = stats["total"]
        wins = stats["wins"]
        results.append(TopSupplier(
            supplier_id=sid,
            supplier_name=user.full_name or user.email,
            supplier_email=user.email,
            total_proposals=total,
            wins=wins,
            win_rate=round(wins / total * 100, 1) if total else 0.0,
        ))

    results.sort(key=lambda x: x.win_rate, reverse=True)
    return results[:limit]


def _top_buyers(db: Session, limit: int = 10) -> list[TopBuyer]:
    """Top buyers by total tender count."""
    buyers = db.query(User).filter(User.role == UserRole.BUYER, User.is_active.is_(True)).all()
    results = []
    for buyer in buyers:
        tenders = db.query(Tender).filter(Tender.created_by == buyer.id).all()
        total_budget = sum(float(t.budget) for t in tenders)
        results.append(TopBuyer(
            buyer_id=buyer.id,
            buyer_name=buyer.full_name or buyer.email,
            buyer_email=buyer.email,
            total_tenders=len(tenders),
            total_budget=total_budget,
        ))
    results.sort(key=lambda x: x.total_tenders, reverse=True)
    return results[:limit]
