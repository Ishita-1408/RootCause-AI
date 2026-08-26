"""Pydantic data models for the RootCause AI Analytics & Metric Engine."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


# ============================================================================
# 1. Headline KPI Summary Models
# ============================================================================
class KPISummary(BaseModel):
    """Consolidated business KPIs across all 6 business categories for a period."""

    start_date: date
    end_date: date

    # Revenue
    gmv: float = Field(..., description="Gross Merchandise Value (BRL)")
    delivered_gmv: float = Field(..., description="GMV for delivered orders (BRL)")
    average_order_value: float | None = Field(
        ..., description="Average order value (BRL)"
    )
    revenue_per_customer: float | None = Field(
        ..., description="Average spend per unique customer (BRL)"
    )

    # Volume
    orders_count: int = Field(..., description="Total orders placed")
    delivered_orders_count: int = Field(..., description="Delivered orders count")
    canceled_orders_count: int = Field(..., description="Canceled orders count")
    items_sold_count: int = Field(..., description="Total product units sold")

    # Customer
    unique_customers_count: int = Field(
        ..., description="Distinct human buyers active in period"
    )
    new_customers_count: int = Field(
        ..., description="First-time buyers acquired in period"
    )
    repeat_customers_count: int = Field(
        ..., description="Active buyers with prior history"
    )
    repeat_buyer_rate_pct: float | None = Field(
        ..., description="Percentage of buyers that are repeat customers (%)"
    )

    # Logistics & Operations
    late_delivery_rate_pct: float | None = Field(
        ..., description="Percentage of delivered orders that arrived late (%)"
    )
    avg_delivery_days: float | None = Field(
        ..., description="Mean total delivery lead time (days)"
    )
    avg_seller_dispatch_days: float | None = Field(
        ..., description="Mean seller handling time (days)"
    )
    avg_carrier_transit_days: float | None = Field(
        ..., description="Mean carrier transit time (days)"
    )

    # Customer Sentiment
    avg_review_score: float | None = Field(
        ..., description="Mean customer rating (1.00 - 5.00)"
    )
    negative_review_rate_pct: float | None = Field(
        ..., description="Percentage of 1 or 2 star ratings (%)"
    )

    # Commercial
    freight_revenue: float = Field(..., description="Total shipping fee revenue (BRL)")
    freight_to_gmv_ratio: float | None = Field(
        ..., description="Freight revenue as proportion of GMV"
    )


# ============================================================================
# 2. Metric Comparison Models
# ============================================================================
class MetricComparison(BaseModel):
    """Deterministic period-over-period comparison for an individual business metric."""

    metric: str
    current_value: float | int | None
    baseline_value: float | int | None
    absolute_change: float | int | None
    percentage_change: float | None
    direction: Literal["increase", "decrease", "unchanged", "undefined"]


class PeriodComparisonResponse(BaseModel):
    """Structured response comparing all business metrics between two periods."""

    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date
    comparisons: dict[str, MetricComparison]


# ============================================================================
# 3. Dimensional Breakdown Models
# ============================================================================
class DimensionalSlice(BaseModel):
    """Attribution metrics for a single slice within a breakdown dimension."""

    slice_value: str
    current_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None
    contribution_percentage: float | None
    rank: int


class DimensionBreakdownResponse(BaseModel):
    """Ranked dimensional attribution and contribution analysis."""

    metric: str
    dimension: str
    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date
    total_current_value: float
    total_baseline_value: float
    total_change: float
    slices: list[DimensionalSlice]


# ============================================================================
# 4. Descriptive Revenue Decomposition Models
# ============================================================================
class RevenueDecomposition(BaseModel):
    """Exact descriptive volume vs. price decomposition of revenue change.

    Note: This is a descriptive mathematical decomposition (Revenue = Orders x AOV),
    not a causal inference model.
    """

    decomposition_type: Literal["descriptive_decomposition"] = (
        "descriptive_decomposition"
    )
    current_start: date
    current_end: date
    baseline_start: date
    baseline_end: date

    current_revenue: float
    baseline_revenue: float
    total_revenue_change: float

    current_orders: int
    baseline_orders: int
    orders_change: int
    orders_change_pct: float | None

    current_aov: float
    baseline_aov: float
    aov_change: float
    aov_change_pct: float | None

    volume_effect: float = Field(
        ...,
        description="Revenue delta attributable to volume change: (V1 - V0) * A0",
    )
    price_effect: float = Field(
        ...,
        description="Revenue delta attributable to AOV change: V1 * (A1 - A0)",
    )


# ============================================================================
# 5. Legacy Phase 5.1 Investigation Models (Maintained for Backward Compatibility)
# ============================================================================
class RevenueInvestigationRequest(BaseModel):
    """Request payload for investigating a revenue change between two periods."""

    start_date: date = Field(
        ...,
        description="Start date of current period (inclusive)",
        examples=["2018-05-01"],
    )
    end_date: date = Field(
        ...,
        description="End date of current period (inclusive)",
        examples=["2018-05-31"],
    )
    baseline_start_date: date = Field(
        ...,
        description="Start date of comparison period (inclusive)",
        examples=["2018-04-01"],
    )
    baseline_end_date: date = Field(
        ...,
        description="End date of comparison period (inclusive)",
        examples=["2018-04-30"],
    )

    @model_validator(mode="after")
    def validate_date_ranges(self) -> "RevenueInvestigationRequest":
        """Ensure date intervals are chronologically valid."""
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        if self.baseline_end_date < self.baseline_start_date:
            raise ValueError(
                "baseline_end_date cannot be earlier than baseline_start_date"
            )
        return self


class PeriodSummary(BaseModel):
    """Financial and volume metrics for a defined time period."""

    start_date: date
    end_date: date
    total_revenue: float = Field(
        ...,
        description="Total merchandise revenue (BRL) from fact_order_analytics",
    )
    order_count: int = Field(..., description="Total order volume")
    average_order_value: float = Field(
        ..., description="Average order value (AOV) in BRL"
    )


class ChangeMetrics(BaseModel):
    """Period-over-period delta metrics and volume/price decomposition."""

    revenue_change: float = Field(
        ..., description="Absolute change in merchandise revenue (BRL)"
    )
    revenue_change_pct: float = Field(
        ..., description="Percentage change in merchandise revenue"
    )
    order_count_change: int = Field(..., description="Absolute change in order count")
    order_count_change_pct: float = Field(
        ..., description="Percentage change in order count"
    )
    aov_change: float = Field(..., description="Absolute change in AOV (BRL)")
    aov_change_pct: float = Field(..., description="Percentage change in AOV")
    volume_effect: float = Field(
        ...,
        description="Revenue change attributable to volume ((V1 - V0) * A0)",
    )
    aov_effect: float = Field(
        ...,
        description="Revenue change attributable to AOV (V1 * (A1 - A0))",
    )


class DimensionFinding(BaseModel):
    """Ranked deterministic finding for a specific dimension value."""

    finding_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the finding",
    )
    dimension: Literal[
        "customer_state", "product_category", "seller", "order_status"
    ] = Field(..., description="Dimension analyzed")
    dimension_value: str = Field(
        ...,
        description="Specific slice value (e.g. SP, health_beauty, delivered)",
    )
    metric: str = Field(default="revenue", description="Target metric")
    current_value: float = Field(..., description="Revenue in current period (BRL)")
    baseline_value: float = Field(..., description="Revenue in baseline period (BRL)")
    absolute_change: float = Field(..., description="Absolute revenue change (BRL)")
    percentage_change: float = Field(
        ..., description="Percentage change for this slice"
    )
    contribution_percentage: float = Field(
        ...,
        description="Share of platform revenue change explained (%)",
    )
    rank: int = Field(..., description="Contribution rank within this dimension")
    explanation: str = Field(
        ..., description="Deterministic, evidence-backed finding explanation"
    )


class RevenueInvestigationResponse(BaseModel):
    """Full structured output returned by the revenue investigation engine."""

    investigation_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the investigation execution",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="Timestamp when the investigation was completed",
    )
    metric: str = Field(default="revenue", description="Business metric investigated")
    current_period: PeriodSummary
    baseline_period: PeriodSummary
    change: ChangeMetrics
    findings: list[DimensionFinding]
