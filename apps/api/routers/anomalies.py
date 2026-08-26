"""FastAPI Router for RootCause AI Time-Series Anomaly Detection (Phase 5A)."""

import logging

import psycopg
from fastapi import APIRouter, HTTPException, status

from apps.analytics.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    run_anomaly_detection,
)
from apps.analytics.change_detection import (
    ChangePointRequest,
    ChangePointSeriesResponse,
    run_change_point_detection,
)
from apps.api.db.connection import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/anomalies",
    tags=["Anomaly Detection"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check for anomaly detection service",
)
def anomalies_health() -> dict[str, str]:
    """Health check for anomaly detection service."""
    return {"status": "healthy", "service": "anomaly_detector"}


@router.post(
    "/detect",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect statistical anomalies across daily KPI time-series",
    description=(
        "Executes a lagged rolling-window z-score anomaly detection across "
        "the requested daily KPI series with zero lookahead data leakage."
    ),
)
def detect_anomalies_endpoint(
    request: AnomalyDetectionRequest,
) -> AnomalyDetectionResponse:
    """Detect statistical anomalies across daily KPI time-series."""
    try:
        with get_db_connection() as conn:
            return run_anomaly_detection(
                conn=conn,
                metric=request.metric,
                start_date=request.start_date,
                end_date=request.end_date,
                product_category=request.product_category,
                window=request.window,
                z_threshold=request.z_threshold,
                minimum_history=request.minimum_history,
            )
    except ValueError as e:
        logger.warning(f"Validation error in anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during anomaly detection.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute anomaly detection.",
        ) from e


@router.post(
    "/change-point",
    response_model=ChangePointSeriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect statistical change points and structural regime shifts",
    description=(
        "Executes Welch's Binary Segmentation change-point detection across "
        "daily KPI time-series to identify persistent mean/variance shifts."
    ),
)
def detect_change_point_endpoint(
    request: ChangePointRequest,
) -> ChangePointSeriesResponse:
    """Detect statistical change points and structural regime shifts."""
    try:
        with get_db_connection() as conn:
            return run_change_point_detection(
                conn=conn,
                metric=request.metric,
                start_date=request.start_date,
                end_date=request.end_date,
                product_category=request.product_category,
                minimum_segment_size=request.minimum_segment_size,
                significance_level=request.significance_level,
                variance_ratio_threshold=request.variance_ratio_threshold,
                method=request.method,
            )
    except ValueError as e:
        logger.warning(f"Validation error in change point detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except psycopg.Error as e:
        logger.error(f"Database error during change point detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable during change point detection.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in change point detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute change point detection.",
        ) from e
