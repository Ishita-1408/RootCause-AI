"""Production Authentication and Role-Based Access Control (RBAC) Module.

Provides a pluggable, secure authentication boundary for RootCause AI:
- Safe local development/demo mode (AUTH_ENABLED=False by default)
- Production API key and Bearer token validation (AUTH_ENABLED=True)
- Role hierarchy: viewer < analyst < admin
- Strictly avoids logging or exposing secrets in client code
"""

import enum
import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from apps.api import config

logger = logging.getLogger("apps.api.auth")

# Security Schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class Role(enum.StrEnum):
    """User access control roles with progressive privileges."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"

    @property
    def level(self) -> int:
        """Numerical privilege rank for hierarchical checks."""
        levels = {
            Role.VIEWER: 1,
            Role.ANALYST: 2,
            Role.ADMIN: 3,
        }
        return levels[self]

    def has_permission(self, required_role: "Role") -> bool:
        """Check if this role satisfies the required role rank."""
        return self.level >= required_role.level


class AuthUser(BaseModel):
    """Authenticated user context."""

    username: str
    role: Role
    is_active: bool = True


def get_current_user(
    api_key: Annotated[str | None, Security(api_key_header)] = None,
    bearer: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)
    ] = None,
) -> AuthUser:
    """Validate incoming request credentials and return authenticated user context.

    In local/demo mode (AUTH_ENABLED=False), returns a default administrative user.
    In protected mode (AUTH_ENABLED=True), validates X-API-Key or Bearer token against
    configured environment secrets.
    """
    settings = config.get_settings()

    # 1. Local / Demo mode: bypass authentication with safe development user
    if not settings.auth_enabled:
        return AuthUser(
            username="local-dev-user",
            role=Role.ADMIN,
            is_active=True,
        )

    # 2. Extract token or API key from request
    token = None
    if bearer and bearer.credentials:
        token = bearer.credentials.strip()
    elif api_key:
        token = api_key.strip()

    if not token:
        logger.warning("Unauthenticated request rejected (missing credentials)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Validate against configured API keys / tokens
    # Admin Key Check
    if settings.admin_api_key and token == settings.admin_api_key:
        return AuthUser(username="admin-service", role=Role.ADMIN, is_active=True)

    # Analyst Key Check
    if settings.analyst_api_key and token == settings.analyst_api_key:
        return AuthUser(username="analyst-user", role=Role.ANALYST, is_active=True)

    # Viewer / Demo Key Check
    if settings.viewer_api_key and token == settings.viewer_api_key:
        return AuthUser(username="viewer-user", role=Role.VIEWER, is_active=True)

    # Reusable default demo token for safe staging
    if token == settings.demo_auth_token:
        return AuthUser(username="demo-analyst", role=Role.ANALYST, is_active=True)

    logger.warning("Unauthorized request rejected (invalid credentials)")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: Role) -> Callable[[AuthUser], AuthUser]:
    """FastAPI dependency factory enforcing minimum role hierarchy."""

    def role_checker(
        current_user: Annotated[AuthUser, Depends(get_current_user)],
    ) -> AuthUser:
        if not current_user.role.has_permission(required_role):
            logger.warning(
                f"Forbidden access: User '{current_user.username}' with role "
                f"'{current_user.role.value}' attempted action requiring "
                f"'{required_role.value}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_role.value}' role privileges.",
            )
        return current_user

    return role_checker
