from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.rbac import require_roles
from app.database import get_db
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(db: Session = Depends(get_db)):
    departments = (
        db.query(Department)
        .options(selectinload(Department.users))
        .order_by(Department.name)
        .all()
    )
    return departments


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    department = Department(**data.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department
