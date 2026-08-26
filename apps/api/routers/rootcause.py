"""FastAPI Router for RootCause AI Deterministic Drill-Down Engine (Phase 5B)."""

import logging

import psycopg
from fastapi import APIRouter, HTTPException, status

from apps.analytics.rootcause import (
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    investigate_root_cause,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/rootcause",
    tags=["Root-Cause Engine"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for root-cause drill-down engine",
)
def rootcause_health() -> dict[str, str]:
    """Health check for root-cause drill-down engine."""
    return {"status": "healthy", "service": "rootcause_engine"}


@router.post(
    "/investigate",
    response_model=RootCauseInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic multi-dimensional root-cause drill-down",
    description=(
        "Compares an observed anomaly date against a preceding baseline period, "
        "calculating exact Volume vs. AOV revenue decomposition, dimensional "
        "slice contributions (Category, State, Seller), and operational indicators."
    ),
)
def investigate_rootcause_endpoint(
    request: RootCauseInvestigationRequest,
) -> RootCauseInvestigationResponse:
    """Execute deterministic multi-dimensional root-cause drill-down."""
    try:
        with get_db_connection() as conn:
            return investigate_root_cause(conn=conn, request=request)
    except ValueError as e:
        logger.warning(f"Validation error in root-cause investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during root-cause investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during root-cause investigation.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in root-cause investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute root-cause investigation.",
        ) from e
