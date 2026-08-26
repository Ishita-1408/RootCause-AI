"""Pydantic data models for Phase 5B Root-Cause Drill-Down Engine."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

APPROVED_METRICS = [
    "total_gmv",
    "orders_count",
    "average_order_value",
    "late_delivery_rate_pct",
    "avg_review_score",
]

APPROVED_DIMENSIONS = [
    "product_category",
    "customer_state",
    "seller",
    "order_volume",
    "average_order_value",
    "delivery",
]


class DimensionContributor(BaseModel):
    """Specific slice contributor within a dimension drill-down."""

    dimension: str
    dimension_value: str
    observed_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None
    contribution_pct: float | None
    direction: Literal["increase", "decrease", "unchanged"]
    rank: int = Field(..., ge=1)


class VolumeValueDecomposition(BaseModel):
    """Exact additive decomposition of GMV delta into volume and AOV effects."""

    observed_orders: float
    baseline_orders: float
    observed_aov: float
    baseline_aov: float
    volume_effect: float = Field(
        ..., description="(observed_orders - baseline_orders) * baseline_aov"
    )
    aov_effect: float = Field(
        ..., description="(observed_aov - baseline_aov) * baseline_orders"
    )
    interaction_effect: float = Field(
        ...,
        description=(
            "(observed_orders - baseline_orders) * (observed_aov - baseline_aov)"
        ),
    )
    total_change: float
    volume_contribution_pct: float | None
    aov_contribution_pct: float | None
    interaction_contribution_pct: float | None


class OperationalIndicators(BaseModel):
    """Fulfillment performance and customer sentiment indicators."""

    observed_late_delivery_rate: float
    baseline_late_delivery_rate: float
    late_delivery_rate_change: float
    observed_avg_delivery_days: float
    baseline_avg_delivery_days: float
    avg_delivery_days_change: float
    observed_cancellation_rate: float
    baseline_cancellation_rate: float
    cancellation_rate_change: float
    observed_avg_review_score: float
    baseline_avg_review_score: float
    avg_review_score_change: float


class RootCauseInvestigationRequest(BaseModel):
    """Input parameters for root-cause investigation."""

    metric: str = Field(
        default="total_gmv",
        description="Approved target metric (e.g. total_gmv, orders_count)",
    )
    anomaly_date: date = Field(..., description="Target anomaly date (YYYY-MM-DD)")
    comparison_days: int = Field(
        default=7,
        ge=1,
        le=60,
        description="Preceding baseline window length in days",
    )
    dimensions: list[str] = Field(
        default_factory=lambda: [
            "product_category",
            "customer_state",
            "seller",
            "order_volume",
            "average_order_value",
            "delivery",
        ],
        description="List of dimensions to investigate",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max ranked contributors per dimension",
    )

    @model_validator(mode="after")
    def validate_inputs(self) -> "RootCauseInvestigationRequest":
        """Validate metric and dimensions against approved registries."""
        norm_metric = self.metric.strip().lower()
        if norm_metric not in APPROVED_METRICS:
            raise ValueError(
                f"Unsupported metric '{self.metric}'. Approved: {APPROVED_METRICS}"
            )
        self.metric = norm_metric

        invalid_dims = [
            d for d in self.dimensions if d.strip().lower() not in APPROVED_DIMENSIONS
        ]
        if invalid_dims:
            raise ValueError(
                f"Invalid dimensions: {invalid_dims}. Approved: {APPROVED_DIMENSIONS}"
            )
        self.dimensions = [d.strip().lower() for d in self.dimensions]
        return self


class AnomalySummary(BaseModel):
    """Headline anomaly summary metrics."""

    metric: str
    anomaly_date: date
    baseline_start_date: date
    baseline_end_date: date
    observed_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None
    direction: Literal["increase", "decrease", "unchanged"]


class RootCauseInvestigationResponse(BaseModel):
    """Complete deterministic root-cause investigation output."""

    request: RootCauseInvestigationRequest
    summary: AnomalySummary
    decomposition: VolumeValueDecomposition | None
    ranked_contributors: list[DimensionContributor]
    operational_indicators: OperationalIndicators
    explanation: str
    limitations: str
