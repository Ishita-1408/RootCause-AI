"""FastAPI Router for Authentication & Profile Telemetry."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from apps.api.auth import AuthUser, Role, get_current_user, require_role
from apps.api.config import Settings, get_settings

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


class AuthStatusResponse(BaseModel):
    """Status of authentication configuration."""

    auth_enabled: bool
    current_user: str
    role: str
    is_active: bool


@router.get(
    "/me",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user and authentication mode status",
)
def get_auth_status(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthStatusResponse:
    """Return active user profile and current authentication enforcement mode."""
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        current_user=current_user.username,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.get(
    "/admin-check",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="RBAC validation endpoint for admin-only privileges",
)
def check_admin_privilege(
    _: Annotated[AuthUser, Depends(require_role(Role.ADMIN))],
) -> dict[str, str]:
    """Test endpoint that requires administrative role privileges."""
    return {"status": "authorized", "privilege": "admin"}
