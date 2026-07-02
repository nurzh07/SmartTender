from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rbac import require_roles
from app.database import get_db
from app.models.tender import Tender
from app.models.user import User, UserRole
from app.services.goszakupki_client import GoszakupkiClient
from app.tasks.goszakupki_tasks import import_open_tenders_from_goszakupki

router = APIRouter()


@router.post("/goszakupki/import")
async def trigger_goszakupki_import(
    limit: int = 10,
    _: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
):
    task = import_open_tenders_from_goszakupki.delay(limit=limit)
    return {"status": "queued", "task_id": task.id}


@router.get("/goszakupki/preview")
async def preview_goszakupki_tenders(
    limit: int = 5,
    _: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
):
    client = GoszakupkiClient()
    return {"items": client.fetch_open_tenders(limit=limit)}


@router.post("/goszakupki/sync/{tender_id}")
async def sync_tender_to_goszakupki(
    tender_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.BUYER, UserRole.SUPERADMIN)),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    client = GoszakupkiClient()
    payload = {
        "title": tender.title,
        "description": tender.description,
        "budget": float(tender.budget),
        "deadline": tender.deadline.isoformat() if tender.deadline else None,
        "internal_id": tender.id,
    }
    result = client.sync_tender(payload)
    return {"tender_id": tender_id, "sync_result": result}
