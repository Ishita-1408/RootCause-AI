"""Pydantic models for Ground Truth Scenarios in RootCause AI Evaluation."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class GroundTruthRootCause(BaseModel):
    """Ground truth target root cause definition with structured causal identifiers."""

    cause_id: str = Field(..., description="Unique identifier for the cause category")
    dimension: str = Field(
        ...,
        description="Target analytical dimension (e.g. order_volume, delivery)",
    )
    dimension_value: str | None = Field(
        default=None,
        description="Specific slice value if applicable (e.g. beleza_saude, SP)",
    )

    # Structured Causal Identifiers (Evaluator v2)
    causal_category: (
        Literal["macro_driver", "operational_mechanism", "segment_concentration"] | str
    ) = Field(
        default="macro_driver",
        description="Classification: macro driver vs operational mechanism vs segment",
    )
    causal_mechanism: str | None = Field(
        default=None,
        description=(
            "Structured causal mechanism (e.g. order_volume, average_order_value, "
            "delivery, carrier_sla)"
        ),
    )
    affected_dimension: str | None = Field(
        default=None,
        description="Target dimension where effect is concentrated",
    )
    affected_value: str | None = Field(
        default=None,
        description="Specific affected slice value if applicable",
    )

    expected_contribution_pct: float | None = Field(
        default=None, description="Expected quantitative contribution % if defined"
    )
    tolerance_pct: float = Field(
        default=15.0,
        description="Acceptable percentage tolerance for quantitative matching",
    )


class GroundTruthScenario(BaseModel):
    """Formal definition of an incident evaluation scenario."""

    scenario_id: str = Field(..., description="Unique scenario ID (e.g. SCN-001)")
    name: str = Field(..., description="Human-readable scenario title")
    description: str = Field(
        ..., description="Detailed business context and incident description"
    )

    # Ground Truth Expectations
    primary_cause: GroundTruthRootCause = Field(
        ..., description="Ground-truth primary root cause"
    )
    secondary_causes: list[GroundTruthRootCause] = Field(
        default_factory=list, description="Valid secondary drivers"
    )
    acceptable_alternative_causes: list[GroundTruthRootCause] = Field(
        default_factory=list,
        description=(
            "Statistically acceptable alternative causes in complex multi-driver cases"
        ),
    )
    distractor_causes: list[str] = Field(
        default_factory=list,
        description="Plausible but non-dominant candidate distractors",
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description=(
            "Scenario difficulty tier: easy (clear single driver), "
            "medium (multi-factor), hard (competing/noisy)"
        ),
    )
    is_insufficient_evidence: bool = Field(
        default=False,
        description=(
            "True if scenario has diffuse or insufficient evidence to establish a "
            "single dominant cause"
        ),
    )

    # Incident Properties
    target_metric: Literal[
        "total_gmv",
        "orders_count",
        "average_order_value",
        "late_delivery_rate_pct",
        "avg_review_score",
    ] = Field(default="total_gmv", description="Target metric evaluated")
    anomaly_date: date = Field(..., description="Date of the anomaly event")
    comparison_days: int = Field(
        default=7, description="Baseline comparison window in days"
    )
    expected_direction: Literal["increase", "decrease", "normal"] = Field(
        default="decrease", description="Observed direction of the metric"
    )
    severity: Literal["normal", "warning", "critical"] = Field(
        default="warning", description="Expected severity"
    )

    # Scope & Evidence Invariants
    affected_dimensions: list[str] = Field(
        default_factory=list,
        description="Dimensions expected to show significant shifts",
    )
    expected_evidence_signals: list[str] = Field(
        default_factory=list,
        description="Key operational signals required to support finding",
    )

    # Metadata
    tags: list[str] = Field(
        default_factory=list,
        description="Domain tags (e.g. logistics, pricing, marketing)",
    )
