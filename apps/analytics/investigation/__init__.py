"""Investigation and contribution package."""

from apps.analytics.investigation.engine import (
    calculate_slice_metrics,
    run_contribution_analysis,
    run_investigation,
)
from apps.analytics.investigation.models import (
    ContributionAnalysis,
    Contributor,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationSummary,
)
from apps.analytics.investigation.queries import (
    SUPPORTED_DIMENSIONS,
    SUPPORTED_METRICS,
    DimensionSliceRecord,
    build_contribution_query,
    fetch_metric_by_dimension,
)
from apps.analytics.investigation_legacy import run_revenue_investigation

__all__ = [
    "SUPPORTED_DIMENSIONS",
    "SUPPORTED_METRICS",
    "ContributionAnalysis",
    "Contributor",
    "DimensionSliceRecord",
    "InvestigationRequest",
    "InvestigationResponse",
    "InvestigationSummary",
    "build_contribution_query",
    "calculate_slice_metrics",
    "fetch_metric_by_dimension",
    "run_contribution_analysis",
    "run_investigation",
    "run_revenue_investigation",
]
