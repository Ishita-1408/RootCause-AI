from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from apps.api.db.connection import check_database_connection

router = APIRouter(tags=["database"])


class DatabaseHealthResponse(BaseModel):
    """Response model for database health check endpoint."""

    status: str
    database: str


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    responses={
        503: {
            "description": "Database connection unavailable",
        }
    },
)
def database_health_check() -> DatabaseHealthResponse:
    """Check database connectivity and return status.

    Returns HTTP 200 with status "ok" if connected,
    or HTTP 503 if unreachable without exposing credentials.
    """
    is_connected = check_database_connection()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        )
    return DatabaseHealthResponse(
        status="ok",
        database="connected",
    )
