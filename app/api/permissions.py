from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.permissions import Permission, RolePermission, UserPermission
from app.core.security import get_current_active_user
from app.core.permissions import PermissionService

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────────
class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str
    module: str
    action: str
    resource: str
    
    class Config:
        from_attributes = True


class RolePermissionCreate(BaseModel):
    role: str
    permission_name: str


class UserPermissionCreate(BaseModel):
    user_id: int
    permission_name: str


# ── Permission Endpoints ───────────────────────────────────────
@router.get("/permissions", response_model=List[PermissionResponse])
async def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Барлық құқықтар
    """
    # Тек superadmin көре алады
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin құқықтарды көре алады"
        )
    
    permissions = db.query(Permission).all()
    return permissions


@router.get("/permissions/my")
async def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Менің құқықтарым
    """
    permissions = PermissionService.get_user_permissions(current_user, db)
    return {
        "user_id": current_user.id,
        "role": current_user.role.value,
        "permissions": permissions
    }


@router.get("/permissions/check/{permission_name}")
async def check_permission(
    permission_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Құқықты тексеру
    """
    has_permission = PermissionService.has_permission(current_user, permission_name, db)
    return {
        "user_id": current_user.id,
        "permission": permission_name,
        "has_permission": has_permission
    }


@router.post("/permissions/initialize")
async def initialize_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Әдепкі құқықтарды инициализациялау
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin инициализациялай алады"
        )
    
    PermissionService.initialize_default_permissions(db)
    
    return {"status": "initialized", "message": "Әдепкі құқықтар инициализацияланды"}


# ── Role Permission Endpoints ─────────────────────────────────
@router.post("/permissions/role/grant")
async def grant_role_permission(
    data: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Рөлге құқық беру
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin құқық бере алады"
        )
    
    success = PermissionService.grant_role_permission(data.role, data.permission_name, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Құқық табылмады"
        )
    
    return {"status": "granted", "role": data.role, "permission": data.permission_name}


@router.post("/permissions/role/revoke")
async def revoke_role_permission(
    data: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Рөлден құқық алу
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin құқық ала алады"
        )
    
    success = PermissionService.revoke_role_permission(data.role, data.permission_name, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Құқық табылмады"
        )
    
    return {"status": "revoked", "role": data.role, "permission": data.permission_name}


@router.get("/permissions/role/{role}")
async def get_role_permissions(
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Рөлдің құқықтары
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin рөл құқықтарын көре алады"
        )
    
    role_permissions = db.query(RolePermission).join(Permission).filter(
        RolePermission.role == role,
        RolePermission.is_granted == True
    ).all()
    
    permissions = [rp.permission.name for rp in role_permissions]
    
    return {
        "role": role,
        "permissions": permissions,
        "count": len(permissions)
    }


# ── User Permission Endpoints ─────────────────────────────────
@router.post("/permissions/user/grant")
async def grant_user_permission(
    data: UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Пайдаланушыға құқық беру
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin құқық бере алады"
    )
    
    success = PermissionService.grant_user_permission(data.user_id, data.permission_name, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Құқық табылмады"
        )
    
    return {"status": "granted", "user_id": data.user_id, "permission": data.permission_name}


@router.post("/permissions/user/revoke")
async def revoke_user_permission(
    data: UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Пайдаланушыдан құқық алу
    """
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек superadmin құқық ала алады"
        )
    
    success = PermissionService.revoke_user_permission(data.user_id, data.permission_name, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Құқық табылмады"
        )
    
    return {"status": "revoked", "user_id": data.user_id, "permission": data.permission_name}


@router.get("/permissions/user/{user_id}")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Пайдаланушының құқықтары
    """
    if current_user.role.value != "superadmin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Құқық жоқ"
        )
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пайдаланушы табылмады"
        )
    
    permissions = PermissionService.get_user_permissions(target_user, db)
    
    return {
        "user_id": user_id,
        "role": target_user.role.value,
        "permissions": permissions
    }
