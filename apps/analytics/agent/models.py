"""Pydantic data models and schemas for Phase 8 Autonomous Investigation Agent."""

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from apps.analytics.change_detection.models import ChangePointResult
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)
from apps.analytics.statistics.models import (
    CausalSupportLevel,
    StatisticalEvidenceSummary,
)

ApprovedMetric = Literal[
    "total_gmv",
    "orders_count",
    "average_order_value",
    "late_delivery_rate_pct",
    "avg_review_score",
]

ApprovedDimension = Literal[
    "product_category",
    "customer_state",
    "seller",
    "order_volume",
    "average_order_value",
    "delivery",
]

StepType = Literal[
    "volume_aov_decomposition",
    "customer_state_drilldown",
    "product_category_drilldown",
    "seller_drilldown",
    "operational_signals_evaluation",
    "customer_sentiment_evaluation",
]

StepStatus = Literal["completed", "skipped", "terminated", "in_progress"]


class InvestigationAgentRequest(BaseModel):
    """Request payload for the Autonomous Investigation Agent."""

    metric: ApprovedMetric = Field(
        default="total_gmv",
        description="Approved KPI metric to investigate autonomously",
    )
    anomaly_date: date = Field(
        ...,
        description="Target anomaly date to investigate (YYYY-MM-DD)",
    )
    comparison_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Preceding baseline window in days",
    )
    dimensions: list[str] = Field(
        default_factory=lambda: [
            "product_category",
            "customer_state",
            "seller",
        ],
        description="Candidate business dimensions for drill-down",
    )
    max_investigation_steps: int = Field(
        default=6,
        ge=1,
        le=12,
        description="Maximum sequential investigation steps before terminating",
    )
    minimum_contribution_pct: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Minimum absolute contribution % for deeper branch exploration",
    )
    minimum_severity: Literal["normal", "warning", "critical"] = Field(
        default="warning",
        description="Minimum anomaly severity threshold",
    )

    @model_validator(mode="after")
    def validate_request(self) -> "InvestigationAgentRequest":
        """Ensure non-empty dimensions and valid parameters."""
        if not self.dimensions:
            raise ValueError("At least one candidate dimension must be provided.")
        return self


class InvestigationStepTrace(BaseModel):
    """Trace entry representing a single step executed or skipped by the agent."""

    step_number: int
    step_type: str
    step_title: str
    status: StepStatus
    finding_summary: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    reason_if_skipped: str | None = None


class RankedRootCause(BaseModel):
    """Single ranked root cause with transparent scoring and evidence chain."""

    rank: int
    title: str
    dimension: str
    dimension_value: str
    contribution_pct: float
    absolute_change: float
    score: float = Field(
        description="Deterministic attribution score based on share & magnitude"
    )
    explanation: str

    # Phase C: Formal Causal Reasoning & Evidence Grounding
    causal_category: Literal[
        "macro_driver", "operational_mechanism", "segment_concentration"
    ] = Field(
        default="macro_driver",
        description="Classification: causal driver vs segment",
    )
    causal_mechanism: str | None = Field(
        default=None,
        description="Underlying mechanism (e.g. delivery, order_volume, aov)",
    )
    affected_dimension: str | None = Field(
        default=None,
        description="Dimension where effect is concentrated",
    )
    affected_value: str | None = Field(
        default=None,
        description="Specific segment value (e.g. SP, MG)",
    )
    evidence_chain: list[str] = Field(
        default_factory=list,
        description="Forensic verification chain (Anomaly -> Driver -> Segment)",
    )
    evidence_strength: Literal["high", "medium", "low", "insufficient"] = Field(
        default="high",
        description="Analytical backing strength against mart metrics",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Statistical confidence score",
    )
    causal_support_level: CausalSupportLevel = Field(
        default="mechanistic",
        description="Causal tier: descriptive, associational, mechanistic, causal",
    )


class InvestigationState(BaseModel):
    """Explicit serializable state machine of the investigation."""

    investigation_id: str = Field(
        default_factory=lambda: f"inv_{uuid.uuid4().hex[:10]}"
    )
    metric: str
    anomaly_date: date
    current_step: int = 0
    max_steps: int = 6
    minimum_contribution_pct: float = 5.0
    completed_steps: list[InvestigationStepTrace] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)
    top_root_causes: list[RankedRootCause] = Field(default_factory=list)
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in findings"
    )
    is_terminated: bool = False
    termination_reason: str | None = None


class EvidenceBackedClaim(BaseModel):
    """Verifiable claim tied deterministically to analytical evidence."""

    evidence_id: str = Field(
        description="Immutable identifier of analytical evidence record"
    )
    claim_type: Literal["anomaly", "causal", "numerical", "operational", "segment"]
    subject: str = Field(description="Exact statement of claim")
    metric: str
    value: float | None = None
    baseline_value: float | None = None
    delta: float | None = None
    percentage_change: float | None = None
    direction: Literal["increase", "decrease", "neutral", "normal"] | None = None
    dimension: str | None = None
    dimension_value: str | None = None
    causal_mechanism: str | None = None
    derived_formula: str | None = None
    is_verified: bool = True
    causal_support_level: CausalSupportLevel = Field(
        default="mechanistic",
        description="Causal identification tier for claim",
    )
    statistical_test: str | None = None
    p_value: float | None = None
    confidence_interval: list[float] | None = None
    effect_size: float | None = None
    sample_size: int | None = None
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] | None = (
        None
    )
    causal_language_level: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Causal hierarchy level 1 to 5",
    )


class InvestigationAgentResponse(BaseModel):
    """Final comprehensive response from the Autonomous Investigation Agent."""

    investigation_id: str
    anomaly_summary: AnomalySummary
    investigation_status: Literal["completed", "early_terminated", "max_steps_reached"]
    steps_executed: int
    trace: list[InvestigationStepTrace]
    decomposition: VolumeValueDecomposition | None = None
    top_root_causes: list[RankedRootCause]
    supporting_evidence: list[DimensionContributor]
    operational_signals: OperationalIndicators
    executive_summary: str
    key_findings: list[str]
    evidence_backed_claims: list[EvidenceBackedClaim] = Field(default_factory=list)
    change_point_analysis: ChangePointResult | None = Field(
        default=None,
        description="Statistical regime shift analysis (temporal evidence)",
    )
    statistical_evidence: StatisticalEvidenceSummary | None = Field(
        default=None,
        description="Detailed statistical confidence evidence (Phase K)",
    )
    evidence_graph: Any | None = Field(
        default=None,
        description="Forensic Evidence Graph (Phase M)",
    )
    recommended_actions: list[str]
    limitations: str
    termination_reason: str
    model: str
    is_fallback: bool
    generated_at: datetime = Field(default_factory=datetime.utcnow)
