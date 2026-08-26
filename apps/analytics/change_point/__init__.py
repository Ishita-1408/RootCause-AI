"""Production-Grade Change-Point and Regime-Shift Detection (Phase L)."""

from apps.analytics.change_point.detectors import (
    detect_cusum_change_point,
    detect_pelt_change_point,
    detect_rolling_baseline,
    detect_welch_binary_segmentation,
    run_change_point_analysis,
)
from apps.analytics.change_point.models import (
    ChangePointRequest,
    ChangePointResult,
    ChangePointSeriesResponse,
    DetectionMethod,
    PersistenceClassification,
    RegimeType,
)
from apps.analytics.change_point.scoring import (
    evaluate_persistence,
    select_detection_method,
)

__all__ = [
    "ChangePointRequest",
    "ChangePointResult",
    "ChangePointSeriesResponse",
    "DetectionMethod",
    "PersistenceClassification",
    "RegimeType",
    "detect_cusum_change_point",
    "detect_pelt_change_point",
    "detect_rolling_baseline",
    "detect_welch_binary_segmentation",
    "evaluate_persistence",
    "run_change_point_analysis",
    "select_detection_method",
]
