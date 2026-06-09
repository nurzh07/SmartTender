from datetime import datetime, timezone

from app.database import SessionLocal, db_transaction
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.services.goszakupki_client import GoszakupkiClient
from app.tasks.celery_app import celery_app


@celery_app.task
def import_open_tenders_from_goszakupki(limit: int = 10) -> dict:
    client = GoszakupkiClient()
    items = client.fetch_open_tenders(limit=limit)
    db = SessionLocal()
    try:
        manager = (
            db.query(User)
            .filter(User.role == UserRole.PROCUREMENT_MANAGER)
            .first()
        )
        creator_id = manager.id if manager else 1

        imported = 0
        with db_transaction(db):
            for item in items:
                ext_id = item.get("external_id")
                if ext_id and db.query(Tender).filter(Tender.external_id == ext_id).first():
                    continue

                deadline_raw = item.get("deadline", "2026-12-31T00:00:00Z")
                deadline = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))

                tender = Tender(
                    title=item.get("title", "Imported tender"),
                    description=item.get("description"),
                    budget=item.get("budget", 0),
                    deadline=deadline,
                    status=TenderStatus.DRAFT,
                    external_id=ext_id,
                    created_by=creator_id,
                    approval_status="imported",
                )
                db.add(tender)
                imported += 1

        return {"imported": imported, "total_fetched": len(items)}
    finally:
        db.close()
