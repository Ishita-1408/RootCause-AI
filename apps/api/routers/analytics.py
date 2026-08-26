"""FastAPI Router for RootCause AI Analytical & KPI Services."""

import logging
from datetime import date
from typing import Annotated

import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from apps.analytics.breakdowns import get_dimensional_breakdown
from apps.analytics.comparison import compare_periods
from apps.analytics.decomposition import get_revenue_decomposition
from apps.analytics.metrics import get_kpis
from apps.analytics.models import (
    DimensionBreakdownResponse,
    KPISummary,
    PeriodComparisonResponse,
    RevenueDecomposition,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)


@router.get(
    "/kpis",
    response_model=KPISummary,
    status_code=status.HTTP_200_OK,
    summary="Retrieve consolidated business KPIs for a date window",
)
def get_kpis_endpoint(
    start_date: Annotated[date, Query(description="Start date (YYYY-MM-DD)")],
    end_date: Annotated[date, Query(description="End date (YYYY-MM-DD)")],
) -> KPISummary:
    """Retrieve consolidated revenue, volume, customer, and logistics KPIs."""
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date cannot be earlier than start_date",
        )

    try:
        with get_db_connection() as conn:
            return get_kpis(conn=conn, start_date=start_date, end_date=end_date)
    except psycopg.Error as e:
        logger.error(f"Database error in get_kpis_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e


@router.get(
    "/compare",
    response_model=PeriodComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare business KPIs between two time windows",
)
def compare_kpis_endpoint(
    current_start: Annotated[date, Query(description="Current period start date")],
    current_end: Annotated[date, Query(description="Current period end date")],
    baseline_start: Annotated[date, Query(description="Baseline period start date")],
    baseline_end: Annotated[date, Query(description="Baseline period end date")],
) -> PeriodComparisonResponse:
    """Compute period-over-period deltas, percentage changes, and directionality."""
    if current_end < current_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_end cannot be earlier than current_start",
        )
    if baseline_end < baseline_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baseline_end cannot be earlier than baseline_start",
        )

    try:
        with get_db_connection() as conn:
            return compare_periods(
                conn=conn,
                current_start=current_start,
                current_end=current_end,
                baseline_start=baseline_start,
                baseline_end=baseline_end,
            )
    except psycopg.Error as e:
        logger.error(f"Database error in compare_kpis_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e


@router.get(
    "/breakdown",
    response_model=DimensionBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform dimensional attribution and contribution analysis",
)
def get_breakdown_endpoint(
    metric: Annotated[
        str, Query(description="Metric to slice (gmv, orders, freight)")
    ] = "gmv",
    dimension: Annotated[
        str,
        Query(
            description=(
                "Dimension (customer_state, product_category, "
                "seller, order_status, payment_type)"
            )
        ),
    ] = "customer_state",
    current_start: Annotated[
        date, Query(description="Current period start date")
    ] = ...,  # type: ignore[assignment]
    current_end: Annotated[date, Query(description="Current period end date")] = ...,  # type: ignore[assignment]
    baseline_start: Annotated[
        date, Query(description="Baseline period start date")
    ] = ...,  # type: ignore[assignment]
    baseline_end: Annotated[date, Query(description="Baseline period end date")] = ...,  # type: ignore[assignment]
    limit: Annotated[int, Query(ge=1, le=100, description="Max slices to return")] = 20,
) -> DimensionBreakdownResponse:
    """Slice KPI changes across dimensions with unclamped contribution."""
    if current_end < current_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_end cannot be earlier than current_start",
        )
    if baseline_end < baseline_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baseline_end cannot be earlier than baseline_start",
        )

    try:
        with get_db_connection() as conn:
            return get_dimensional_breakdown(
                conn=conn,
                metric=metric,
                dimension=dimension,
                current_start=current_start,
                current_end=current_end,
                baseline_start=baseline_start,
                baseline_end=baseline_end,
                limit=limit,
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error in get_breakdown_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e


@router.get(
    "/decomposition",
    response_model=RevenueDecomposition,
    status_code=status.HTTP_200_OK,
    summary="Decompose revenue change into volume vs. price (AOV) effects",
)
def get_decomposition_endpoint(
    current_start: Annotated[date, Query(description="Current period start date")],
    current_end: Annotated[date, Query(description="Current period end date")],
    baseline_start: Annotated[date, Query(description="Baseline period start date")],
    baseline_end: Annotated[date, Query(description="Baseline period end date")],
) -> RevenueDecomposition:
    """Perform descriptive volume vs. price mathematical decomposition."""
    if current_end < current_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="current_end cannot be earlier than current_start",
        )
    if baseline_end < baseline_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baseline_end cannot be earlier than baseline_start",
        )

    try:
        with get_db_connection() as conn:
            return get_revenue_decomposition(
                conn=conn,
                current_start=current_start,
                current_end=current_end,
                baseline_start=baseline_start,
                baseline_end=baseline_end,
            )
    except psycopg.Error as e:
        logger.error(f"Database error in get_decomposition_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from e
