"""Pydantic data models for Phase 5B Deterministic Root-Cause Contribution Engine."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Contributor(BaseModel):
    """Specific slice contributor within a business dimension."""

    dimension: str
    value: str
    current_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None = Field(
        None,
        description="Percentage change (None if baseline is 0)",
    )
    contribution_pct: float | None = Field(
        None,
        description="Unclamped contribution percentage to total KPI change",
    )
    rank: int = Field(..., ge=1, description="Rank within positive/negative list")


class ContributionAnalysis(BaseModel):
    """Contribution analysis across a single business dimension."""

    metric: str
    dimension: str
    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date
    total_current: float
    total_baseline: float
    total_change: float
    total_change_pct: float | None
    top_negative_contributors: list[Contributor] = Field(
        default_factory=list,
        description="Top slices driving decline (sorted most negative first)",
    )
    top_positive_contributors: list[Contributor] = Field(
        default_factory=list,
        description="Top slices driving growth (sorted largest gain first)",
    )
    all_contributors_count: int = Field(
        ..., description="Total distinct slice values evaluated"
    )


class InvestigationRequest(BaseModel):
    """Request payload for multi-dimensional root-cause contribution analysis."""

    metric: str = Field(
        default="total_gmv",
        description=(
            "Target KPI (total_gmv, orders_count, average_order_value, "
            "late_delivery_rate_pct, avg_review_score)"
        ),
    )
    current_start: date = Field(
        ..., description="Current period start date (YYYY-MM-DD)"
    )
    current_end: date = Field(..., description="Current period end date (YYYY-MM-DD)")
    baseline_start: date = Field(
        ..., description="Baseline period start date (YYYY-MM-DD)"
    )
    baseline_end: date = Field(..., description="Baseline period end date (YYYY-MM-DD)")
    dimensions: list[str] = Field(
        default_factory=lambda: [
            "customer_state",
            "product_category_name",
            "seller_id",
        ],
        description=(
            "Dimensions to analyze (customer_state, product_category_name, "
            "seller_id, order_status, payment_type)"
        ),
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "InvestigationRequest":
        """Validate that end dates are not earlier than start dates."""
        if self.current_end < self.current_start:
            raise ValueError("current_end cannot be earlier than current_start")
        if self.baseline_end < self.baseline_start:
            raise ValueError("baseline_end cannot be earlier than baseline_start")
        return self


class InvestigationSummary(BaseModel):
    """High-level deterministic summary of the multi-dimensional investigation."""

    metric: str
    direction: Literal["increase", "decrease", "unchanged", "undefined"]
    total_current: float
    total_baseline: float
    total_change: float
    total_change_pct: float | None
    primary_negative_dimension: str | None = None
    primary_negative_contributor: str | None = None
    primary_positive_dimension: str | None = None
    primary_positive_contributor: str | None = None


class InvestigationResponse(BaseModel):
    """Complete structured output of the root-cause contribution investigation."""

    request: InvestigationRequest
    summary: InvestigationSummary
    analyses: list[ContributionAnalysis]
