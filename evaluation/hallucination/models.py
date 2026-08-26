"""Structured Claim & Evidence Models for Phase G.

Adversarial Hallucination Evaluation.
"""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from apps.analytics.statistics.models import CausalSupportLevel

ClaimType = Literal[
    "anomaly",
    "numerical",
    "causal",
    "segment",
    "trend",
    "operational",
    "recommendation",
]

VerificationStatus = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTED",
]

ClaimUnit = Literal[
    "BRL",
    "orders",
    "days",
    "pct",
    "score",
    "ratio",
    "count",
    "none",
]


class EvidenceRecord(BaseModel):
    """Deterministic verifiable empirical evidence extracted from database or engine."""

    evidence_id: str = Field(description="Unique deterministic identifier for evidence")
    source: str = Field(description="Database table, query mart, or analytical engine")
    metric: str = Field(
        description="Target business metric (e.g. total_gmv, orders_count)"
    )
    observed_value: float = Field(description="Observed KPI value on anomaly date")
    baseline_value: float | None = Field(
        default=None, description="Baseline KPI mean across comparison window"
    )
    delta: float | None = Field(
        default=None, description="Absolute change (Observed - Baseline)"
    )
    delta_pct: float | None = Field(
        default=None,
        description="Percentage change ((Observed - Baseline) / Baseline) * 100",
    )
    direction: Literal["increase", "decrease", "neutral", "normal"] = Field(
        default="neutral", description="Statistical direction of variance"
    )
    dimension: str | None = Field(
        default=None,
        description="Analytical dimension (e.g. customer_state, product_category)",
    )
    dimension_value: str | None = Field(
        default=None, description="Specific segment value (e.g. SP, cama_mesa_banho)"
    )
    anomaly_date: date = Field(description="Target date of observation")
    comparison_window: int = Field(default=7, description="Window size in days")
    query_tool_id: str | None = Field(
        default=None, description="Tool / Query function generating evidence"
    )
    raw_details: dict[str, Any] = Field(
        default_factory=dict, description="Raw dictionary from database query"
    )
    causal_support_level: CausalSupportLevel = Field(
        default="mechanistic",
        description="Causal identification tier of supporting evidence",
    )
    statistical_test: str | None = None
    p_value: float | None = None
    confidence_interval: list[float] | None = None
    effect_size: float | None = None
    sample_size: int | None = None
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] | None = (
        None
    )
    causal_language_level: int = Field(default=3, ge=1, le=5)


class StructuredClaim(BaseModel):
    """Structured, typed representation of a factual, numerical, or causal claim."""

    claim_id: str = Field(description="Unique identifier for the claim")
    claim_type: ClaimType = Field(description="Category of the claim")
    metric: str = Field(description="Subject metric (e.g. total_gmv, orders_count)")
    subject: str = Field(description="Human readable subject or statement summary")
    value: float | None = Field(
        default=None, description="Claimed numerical quantity or metric value"
    )
    unit: str | None = Field(
        default=None, description="Unit of measurement (BRL, orders, pct, etc.)"
    )
    direction: Literal["increase", "decrease", "neutral", "normal"] | None = Field(
        default=None, description="Claimed direction of movement"
    )
    dimension: str | None = Field(default=None, description="Claimed dimension")
    dimension_value: str | None = Field(
        default=None, description="Claimed segment slice value"
    )
    anomaly_date: date | None = Field(default=None, description="Claimed anomaly date")
    comparison_window: int | None = Field(
        default=None, description="Claimed comparison window in days"
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="Explicit IDs of supporting evidence records"
    )
    causal_mechanism: str | None = Field(
        default=None,
        description=(
            "Underlying causal mechanism (order_volume, average_order_value, delivery)"
        ),
    )
    derived_formula: str | None = Field(
        default=None,
        description=(
            "Derived formula type (percentage_change, contribution_percentage, "
            "volume_effect, aov_effect, absolute_change)"
        ),
    )
    causal_support_level: CausalSupportLevel = Field(
        default="associational",
        description="Causal support level asserted by the claim",
    )
    statistical_test: str | None = None
    p_value: float | None = None
    confidence_interval: list[float] | None = None
    effect_size: float | None = None
    sample_size: int | None = None
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] | None = (
        None
    )
    causal_language_level: int = Field(default=3, ge=1, le=5)


class ClaimVerificationResult(BaseModel):
    """Result of evaluating a single claim against matched evidence."""

    claim_id: str
    verification_status: VerificationStatus
    claimed_value: float | None = None
    evidence_value: float | None = None
    absolute_error: float | None = None
    relative_error_pct: float | None = None
    allowed_tolerance: float = 0.05
    failure_reason: str | None = None
    evidence_matched_id: str | None = None


class ClaimBenchmarkSummary(BaseModel):
    """Aggregate forensic metrics for claim-level hallucination evaluation."""

    total_claims: int
    supported_count: int
    partially_supported_count: int
    unsupported_count: int
    contradicted_count: int

    # Core rates (percentages 0.0 - 100.0)
    claim_grounding_rate: float = Field(
        description="Percentage of claims that are SUPPORTED or PARTIALLY_SUPPORTED"
    )
    unsupported_claim_rate: float = Field(
        description="Percentage of claims with missing/unsupported evidence"
    )
    contradiction_rate: float = Field(
        description="Percentage of claims that contradict empirical evidence"
    )
    hallucination_rate: float = Field(
        description="Percentage of claims that are UNSUPPORTED or CONTRADICTED"
    )

    # Precision & Attribution Metrics
    numerical_accuracy: float = Field(
        description="Accuracy of exact numerical assertions within tolerance"
    )
    evidence_attribution_accuracy: float = Field(
        description=(
            "Percentage of valid evidence IDs that directly corroborate the claim"
        )
    )
    claim_precision: float = Field(
        description="Precision: Supported / (Supported + Unsupported + Contradicted)"
    )
    claim_recall: float = Field(
        description="Recall: Supported claims out of all material scenario truths"
    )

    results: list[ClaimVerificationResult] = Field(default_factory=list)
