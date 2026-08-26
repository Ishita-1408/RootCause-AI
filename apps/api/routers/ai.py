"""FastAPI Router for RootCause AI Executive Investigation Layer (Phase 5C)."""

import logging

import psycopg
from fastapi import APIRouter, HTTPException, status

from apps.ai import (
    AIInvestigationResponse,
    investigate_with_ai,
)
from apps.analytics.rootcause import (
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    investigate_root_cause,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Investigation"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for AI investigation service",
)
def ai_health() -> dict[str, str]:
    """Health check for AI investigation service."""
    return {"status": "healthy", "service": "ai_investigator"}


@router.post(
    "/investigate",
    response_model=AIInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute end-to-end deterministic + AI executive investigation",
    description=(
        "Executes a deterministic root-cause investigation against analytical "
        "marts, validates numerical evidence, and synthesizes a structured "
        "executive business memo via the AI explanation layer."
    ),
)
def ai_investigate_endpoint(
    request: RootCauseInvestigationRequest,
) -> AIInvestigationResponse:
    """Execute end-to-end deterministic + AI executive investigation."""
    try:
        with get_db_connection() as conn:
            root_cause_resp = investigate_root_cause(conn=conn, request=request)
        return investigate_with_ai(root_cause_response=root_cause_resp)
    except ValueError as e:
        logger.warning(f"Validation error in AI investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during AI investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during AI investigation.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during AI investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI executive investigation.",
        ) from e


@router.post(
    "/explain",
    response_model=AIInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate executive AI memo from pre-computed root-cause evidence",
    description=(
        "Synthesizes an executive memo directly from pre-computed deterministic "
        "RootCauseInvestigationResponse evidence without querying the database."
    ),
)
def ai_explain_endpoint(
    request: RootCauseInvestigationResponse,
) -> AIInvestigationResponse:
    """Generate executive AI memo from pre-computed root-cause evidence."""
    try:
        return investigate_with_ai(root_cause_response=request)
    except Exception as e:
        logger.error(f"Unexpected error in ai_explain_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI explanation.",
        ) from e
