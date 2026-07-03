"""Барлық тендерлерді және байланысты деректерді өшіру."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.cache import invalidate_tenders_cache
from app.database import SessionLocal
from app.models.approval import ApprovalWorkflow
from app.models.proposal import TenderProposal
from app.models.supplier_rating import SupplierRating
from app.models.tender import Tender


def clean_tenders() -> None:
    db = SessionLocal()
    try:
        proposals = db.query(TenderProposal).delete()
        approvals = db.query(ApprovalWorkflow).delete()
        ratings = db.query(SupplierRating).delete()
        db.execute(text("DELETE FROM tender_audit_log"))
        tenders = db.query(Tender).delete()
        db.commit()
        invalidate_tenders_cache()
        print(
            f"Тазартылды: {tenders} тендер, {proposals} ұсыныс, "
            f"{approvals} бекіту, {ratings} рейтинг"
        )
    finally:
        db.close()


if __name__ == "__main__":
    clean_tenders()
