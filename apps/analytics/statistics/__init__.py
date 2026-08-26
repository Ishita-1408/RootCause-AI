"""Statistical Confidence, Significance, and Causal Guardrails Module (Phase K)."""

from apps.analytics.statistics.causal_guardrails import (
    sanitize_causal_language,
    validate_causal_language,
)
from apps.analytics.statistics.intervals import (
    compute_bootstrap_confidence_interval,
    compute_mean_confidence_interval,
    compute_proportion_confidence_interval,
    compute_welch_confidence_interval,
)
from apps.analytics.statistics.models import (
    CausalSupportLevel,
    ConfidenceInterval,
    DriverStatisticalEvidence,
    StatisticalEstimate,
    StatisticalEvidenceSummary,
    StatisticalSignificance,
    TemporalStatisticalEvidence,
)
from apps.analytics.statistics.summary import build_statistical_evidence_summary

__all__ = [
    "CausalSupportLevel",
    "ConfidenceInterval",
    "DriverStatisticalEvidence",
    "StatisticalEstimate",
    "StatisticalEvidenceSummary",
    "StatisticalSignificance",
    "TemporalStatisticalEvidence",
    "build_statistical_evidence_summary",
    "compute_bootstrap_confidence_interval",
    "compute_mean_confidence_interval",
    "compute_proportion_confidence_interval",
    "compute_welch_confidence_interval",
    "sanitize_causal_language",
    "validate_causal_language",
]
