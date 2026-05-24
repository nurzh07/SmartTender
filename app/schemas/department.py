from pydantic import BaseModel
from decimal import Decimal


class DepartmentBase(BaseModel):
    name: str
    budget_limit: Decimal = Decimal("0")
    head_user_id: int | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    budget_limit: Decimal | None = None
    head_user_id: int | None = None


class DepartmentResponse(DepartmentBase):
    id: int

    class Config:
        from_attributes = True
