"""FastAPI Router for RootCause AI Business Investigations."""

import logging

import psycopg
from fastapi import APIRouter, HTTPException, status

from apps.analytics.dimension_registry import DimensionDefinition, DimensionRegistry
from apps.analytics.investigation import (
    InvestigationRequest,
    InvestigationResponse,
    run_investigation,
)
from apps.analytics.investigation_legacy import (
    run_revenue_investigation,
)
from apps.analytics.models import (
    RevenueInvestigationRequest,
    RevenueInvestigationResponse,
)
from apps.analytics.narrator import (
    InvestigationNarrative,
    NarrativeRequest,
    generate_investigation_narrative,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/investigations",
    tags=["Investigations"],
)


@router.get(
    "/dimensions",
    response_model=list[DimensionDefinition],
    status_code=status.HTTP_200_OK,
    summary="List safe whitelisted analytical drill-down dimensions",
    description=(
        "Returns metadata for all approved dimensional drill-downs in RootCause AI."
    ),
)
def list_dimensions_endpoint() -> list[DimensionDefinition]:
    """Return all whitelisted drill-down dimensions."""
    return DimensionRegistry.list_dimensions()


@router.post(
    "/narrative",
    response_model=InvestigationNarrative,
    status_code=status.HTTP_200_OK,
    summary="Generate executive AI narrative from verified investigation evidence",
    description=(
        "Converts a verified InvestigationResponse into a structured executive "
        "root-cause narrative using an LLM (if configured) or deterministic fallback."
    ),
)
def generate_narrative_endpoint(
    request: NarrativeRequest,
) -> InvestigationNarrative:
    """Generate structured narrative from verified investigation response."""
    try:
        return generate_investigation_narrative(investigation=request.investigation)
    except Exception as e:
        logger.error(f"Unexpected error in generate_narrative_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate investigation narrative.",
        ) from e


@router.post(
    "/contributions",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-dimensional root-cause contribution analysis",
    description=(
        "Executes a deterministic root-cause contribution analysis comparing "
        "any supported KPI between two periods across multiple business dimensions, "
        "returning ranked top positive and top negative contributors."
    ),
)
def investigate_contributions_endpoint(
    request: InvestigationRequest,
) -> InvestigationResponse:
    """Execute deterministic multi-dimensional root-cause contribution investigation."""
    try:
        with get_db_connection() as conn:
            return run_investigation(conn=conn, request=request)
    except ValueError as e:
        logger.warning(f"Validation error in contributions investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during contributions investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during investigation.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during contributions investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute contribution investigation.",
        ) from e


@router.post(
    "/revenue",
    response_model=RevenueInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Investigate revenue change between two periods (Legacy Phase 5.1)",
    description=(
        "Executes a deterministic root-cause analysis comparing revenue "
        "between two periods, returning exact volume/AOV decompositions and "
        "dimensional contribution rankings."
    ),
)
def investigate_revenue_endpoint(
    request: RevenueInvestigationRequest,
) -> RevenueInvestigationResponse:
    """Execute deterministic period-over-period revenue investigation."""
    try:
        with get_db_connection() as conn:
            return run_revenue_investigation(request=request, conn=conn)
    except psycopg.Error as e:
        logger.error(f"Database error during revenue investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during investigation.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute revenue investigation.",
        ) from e
