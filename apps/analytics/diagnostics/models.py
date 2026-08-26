"""Pydantic data models for Phase 5B Root-Cause Diagnostic Engine."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DiagnosticSummary(BaseModel):
    """High-level summary of the diagnostic investigation."""

    metric: str
    anomaly_date: date
    comparison_period_start: date
    comparison_period_end: date
    baseline_period_start: date
    baseline_period_end: date
    actual_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None
    primary_driver: Literal[
        "ORDER_VOLUME",
        "AVERAGE_ORDER_VALUE",
        "FULFILLMENT_PERFORMANCE",
        "CUSTOMER_SATISFACTION",
        "STABLE_OR_BALANCED",
    ]
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class RevenueDecomposition(BaseModel):
    """Exact additive decomposition of revenue delta into Volume, AOV, and Interaction."""  # noqa: E501

    volume_effect: float = Field(..., description="Delta V * A_base")
    aov_effect: float = Field(..., description="V_base * Delta A")
    interaction_effect: float = Field(..., description="Delta V * Delta A")
    total_revenue_change: float = Field(..., description="Actual - Baseline Revenue")
    volume_contribution_pct: float | None = Field(
        None, description="Volume effect as percentage of total change"
    )
    aov_contribution_pct: float | None = Field(
        None, description="AOV effect as percentage of total change"
    )
    interaction_contribution_pct: float | None = Field(
        None, description="Interaction effect as percentage of total change"
    )


class DimensionFinding(BaseModel):
    """Slice attribution finding within a business dimension."""

    dimension: str
    dimension_value: str
    actual_value: float
    baseline_value: float
    change: float
    percentage_change: float | None
    contribution_pct: float | None
    rank: int = Field(..., ge=1)


class OperationalFinding(BaseModel):
    """Operational fulfillment performance finding."""

    metric: str
    actual_value: float
    baseline_value: float
    change: float
    percentage_change: float | None
    severity: Literal["normal", "warning", "critical"]


class SatisfactionFinding(BaseModel):
    """Customer review and sentiment finding."""

    metric: str
    actual_value: float
    baseline_value: float
    change: float
    percentage_change: float | None
    sentiment_impact: Literal["positive", "neutral", "negative"]


class RootCauseFinding(BaseModel):
    """Ranked root-cause candidate with transparent multi-factor score."""

    rank: int = Field(..., ge=1)
    cause: str
    category: Literal[
        "VOLUME",
        "PRICING_AOV",
        "DIMENSION_CONCENTRATION",
        "OPERATIONAL_FULFILLMENT",
        "CUSTOMER_SATISFACTION",
    ]
    score: float = Field(..., ge=0.0, le=1.0)
    contribution: str
    evidence: str


class DiagnosticRequest(BaseModel):
    """Request payload for automated root-cause diagnostic investigation."""

    metric: str = Field(
        default="total_gmv",
        description=(
            "Target metric (total_gmv, orders_count, average_order_value, "
            "late_delivery_rate_pct, avg_review_score)"
        ),
    )
    anomaly_date: date = Field(..., description="Reference anomaly date (YYYY-MM-DD)")
    comparison_window: int = Field(
        default=7, ge=1, le=90, description="Comparison window length in days"
    )
    baseline_window: int = Field(
        default=28, ge=1, le=180, description="Baseline window length in days"
    )
    category: str | None = Field(
        default=None, description="Optional product category filter"
    )
    customer_state: str | None = Field(
        default=None, description="Optional customer state filter"
    )

    @model_validator(mode="after")
    def validate_windows(self) -> "DiagnosticRequest":
        """Validate window consistency."""
        if self.baseline_window < self.comparison_window:
            raise ValueError(
                "baseline_window must be at least as large as comparison_window"
            )
        return self


class DiagnosticResponse(BaseModel):
    """Complete diagnostic output with multi-layer root-cause findings."""

    request: DiagnosticRequest
    summary: DiagnosticSummary
    revenue_decomposition: RevenueDecomposition | None
    top_dimensional_contributors: list[DimensionFinding]
    operational_signals: list[OperationalFinding]
    satisfaction_signals: list[SatisfactionFinding]
    root_cause_ranking: list[RootCauseFinding]
    conclusion: str
