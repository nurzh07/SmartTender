from fastapi import APIRouter, Depends, HTTPException

from app.core.rbac import require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.services.odoo_client import OdooClient
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/employees")
async def fetch_employees(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.BUYER)),
):
    """Odoo ERP-ден қызметкерлер тізімін алу."""
    try:
        client = OdooClient()
        employees = client.fetch_employees()
        return {"status": "success", "count": len(employees), "data": employees}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Odoo integration failed: {exc}")


@router.post("/sync-employee/{employee_id}")
async def sync_employee(
    employee_id: int,
    employee_data: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    """Қызметкер деректерін Odoo-ға синхрондау."""
    try:
        client = OdooClient()
        result = client.sync_employee({"id": employee_id, **employee_data})
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Odoo sync failed: {exc}")
