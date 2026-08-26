"""Health and readiness check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from apps.api.config import Settings, get_settings
from apps.api.db.connection import check_database_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    app: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Response model for readiness check endpoint."""

    status: str
    database: str
    app: str
    version: str


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Return application liveness status and basic metadata."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
@router.get("/api/v1/ready", response_model=ReadinessResponse)
def readiness_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessResponse:
    """Check readiness by verifying database connectivity."""
    is_db_ready = check_database_connection()
    if not is_db_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )
    return ReadinessResponse(
        status="ready",
        database="connected",
        app=settings.app_name,
        version=settings.app_version,
    )
