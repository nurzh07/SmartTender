"""
Analytics Pydantic schemas.
"""

from pydantic import BaseModel
from typing import Any


# ── Stat cards ──────────────────────────────────────────────────

class MonthlyBar(BaseModel):
    month: str          # "2025-01"
    month_label: str    # "Qаңтар"
    count: int
    budget: float = 0.0


class StatusPie(BaseModel):
    status: str
    count: int
    label: str


class TopSupplier(BaseModel):
    supplier_id: int
    supplier_name: str
    supplier_email: str
    total_proposals: int
    wins: int
    win_rate: float


class TopBuyer(BaseModel):
    buyer_id: int
    buyer_name: str
    buyer_email: str
    total_tenders: int
    total_budget: float


# ── Buyer Dashboard ──────────────────────────────────────────────

class BuyerDashboard(BaseModel):
    total_tenders_this_month: int
    total_tenders_last_month: int
    total_budget_awarded: float
    avg_proposals_per_tender: float
    top_suppliers: list[TopSupplier]
    status_distribution: list[StatusPie]
    monthly_activity: list[MonthlyBar]


# ── Supplier Dashboard ───────────────────────────────────────────

class SupplierDashboard(BaseModel):
    total_proposals: int
    win_rate: float
    avg_own_price: float
    avg_market_price: float
    monthly_activity: list[MonthlyBar]
    wins_losses: list[StatusPie]


# ── Admin Dashboard ──────────────────────────────────────────────

class AdminDashboard(BaseModel):
    total_users: int
    total_buyers: int
    total_suppliers: int
    total_tenders: int
    total_transaction_volume: float
    status_distribution: list[StatusPie]
    monthly_activity: list[MonthlyBar]
    top_buyers: list[TopBuyer]
    top_suppliers: list[TopSupplier]
