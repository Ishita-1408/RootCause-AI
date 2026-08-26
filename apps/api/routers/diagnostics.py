"""FastAPI Router for RootCause AI Diagnostic Engine."""

import logging

import psycopg
from fastapi import APIRouter, HTTPException, status

from apps.analytics.diagnostics import (
    DiagnosticRequest,
    DiagnosticResponse,
    run_root_cause_analysis,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/diagnostics",
    tags=["Diagnostics"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for diagnostic engine",
)
def diagnostics_health() -> dict[str, str]:
    """Health check for diagnostic engine."""
    return {"status": "healthy", "service": "diagnostics_engine"}


@router.post(
    "/root-cause",
    response_model=DiagnosticResponse,
    status_code=status.HTTP_200_OK,
    summary="Automated multi-layer root-cause diagnostic investigation",
    description=(
        "Executes a comprehensive deterministic diagnostic analysis including "
        "Volume vs AOV decomposition, dimensional drill-downs, operational "
        "fulfillment signals, and candidate root-cause scoring."
    ),
)
def root_cause_diagnostic_endpoint(
    request: DiagnosticRequest,
) -> DiagnosticResponse:
    """Execute automated root-cause diagnostic investigation."""
    try:
        with get_db_connection() as conn:
            return run_root_cause_analysis(conn=conn, request=request)
    except ValueError as e:
        logger.warning(f"Validation error in root-cause diagnostics: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during root-cause diagnostics: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during diagnostics.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during root-cause diagnostics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute root-cause diagnostic analysis.",
        ) from e
