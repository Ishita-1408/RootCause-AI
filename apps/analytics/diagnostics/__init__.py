"""Diagnostic Engine Package."""

from apps.analytics.diagnostics.engine import run_root_cause_analysis
from apps.analytics.diagnostics.models import (
    DiagnosticRequest,
    DiagnosticResponse,
    DiagnosticSummary,
    DimensionFinding,
    OperationalFinding,
    RevenueDecomposition,
    RootCauseFinding,
    SatisfactionFinding,
)
from apps.analytics.diagnostics.queries import (
    DiagnosticSliceRecord,
    PeriodAggregateRecord,
    fetch_dimension_slices_for_diagnostic,
    fetch_period_diagnostics,
)
from apps.analytics.diagnostics.scorers import (
    compute_root_cause_score,
    rank_candidate_root_causes,
)

__all__ = [
    "DiagnosticRequest",
    "DiagnosticResponse",
    "DiagnosticSliceRecord",
    "DiagnosticSummary",
    "DimensionFinding",
    "OperationalFinding",
    "PeriodAggregateRecord",
    "RevenueDecomposition",
    "RootCauseFinding",
    "SatisfactionFinding",
    "compute_root_cause_score",
    "fetch_dimension_slices_for_diagnostic",
    "fetch_period_diagnostics",
    "rank_candidate_root_causes",
    "run_root_cause_analysis",
]
