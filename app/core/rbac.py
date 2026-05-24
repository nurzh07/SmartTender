from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_active_user
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable:
    """RBAC dependency: only listed roles may access the endpoint."""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not allowed",
            )
        return current_user

    return role_checker
