from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DailyKPIObservation(BaseModel):
    """Single daily observation of a KPI metric."""

    date: date
    metric: str
    value: float | None


class AnomalyResult(BaseModel):
    """Statistical anomaly evaluation for a single date observation."""

    date: date
    metric: str
    observed_value: float | None
    baseline_mean: float | None = Field(
        None, description="Lagged rolling mean excluding the evaluated date"
    )
    baseline_std: float | None = Field(
        None,
        description="Lagged rolling standard deviation excluding evaluated date",
    )
    z_score: float | None = Field(
        None, description="Standardized deviation score (z = (x - mu) / sigma)"
    )
    severity: Literal["normal", "warning", "critical"] = Field(
        default="normal",
        description="Severity classification based on z-score magnitude",
    )
    is_anomaly: bool = Field(
        default=False,
        description="True if |z_score| exceeds configured z_threshold",
    )
    direction: Literal["increase", "decrease", "normal"] = Field(
        default="normal", description="Direction of the anomalous movement"
    )


class AnomalyDetectionRequest(BaseModel):
    """Request payload for daily time-series statistical anomaly detection."""

    metric: str = Field(
        default="total_gmv",
        description="Target metric (e.g. total_gmv, orders_count, average_order_value)",
    )
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")
    product_category: str | None = Field(
        default=None, description="Optional product category filter"
    )
    window: int = Field(
        default=7, ge=1, le=90, description="Rolling window size in days"
    )
    z_threshold: float = Field(
        default=2.0, gt=0.0, le=10.0, description="Z-score threshold for anomalies"
    )
    minimum_history: int = Field(
        default=7, ge=1, le=90, description="Minimum observations before evaluating"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "AnomalyDetectionRequest":
        """Validate date sequence."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AnomalyDetectionResponse(BaseModel):
    """Consolidated time-series anomaly detection report."""

    metric: str
    product_category: str | None = None
    start_date: date
    end_date: date
    window: int
    z_threshold: float
    minimum_history: int
    total_observations: int
    anomalies_count: int
    results: list[AnomalyResult]
    change_point: Any | None = Field(
        default=None,
        description="Optional statistical change-point analysis over the series",
    )
