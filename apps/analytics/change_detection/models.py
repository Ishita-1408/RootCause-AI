"""Pydantic data models for Statistical Change-Point Detection (Phase J)."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from apps.analytics.anomaly.models import DailyKPIObservation

RegimeType = Literal[
    "normal",
    "isolated_anomaly",
    "sustained_level_shift",
    "variance_regime_shift",
    "gradual_trend",
    "insufficient_data",
]


class ChangePointResult(BaseModel):
    """Statistical change-point evaluation result for a time series."""

    metric: str = Field(..., description="Target metric name")
    change_point_detected: bool = Field(
        ..., description="True if a statistically significant change point was found"
    )
    change_point_date: date | None = Field(
        default=None, description="Date where structural regime shift occurred"
    )
    regime_type: RegimeType = Field(
        default="normal",
        description=(
            "Classified statistical regime: normal, isolated_anomaly, "
            "sustained_level_shift, variance_regime_shift, gradual_trend, "
            "or insufficient_data"
        ),
    )
    pre_change_mean: float | None = Field(
        default=None,
        description="Mean of the segment prior to candidate change point",
    )
    post_change_mean: float | None = Field(
        default=None,
        description="Mean of the segment after candidate change point",
    )
    mean_shift_pct: float | None = Field(
        default=None,
        description="Percentage change in segment means ((mu2 - mu1) / mu1 * 100)",
    )
    pre_change_variance: float | None = Field(
        default=None,
        description="Sample variance of the pre-change segment",
    )
    post_change_variance: float | None = Field(
        default=None,
        description="Sample variance of the post-change segment",
    )
    variance_ratio: float | None = Field(
        default=None,
        description="Ratio of maximum to minimum segment variance (s2^2 / s1^2)",
    )
    statistical_score: float | None = Field(
        default=None,
        description="Interpretable test statistic magnitude (|t| or F-stat)",
    )
    test_statistic: float | None = Field(
        default=None,
        description="Welch's two-sample t-statistic for mean difference",
    )
    p_value: float | None = Field(
        default=None,
        description="Two-tailed p-value from Welch's t-test",
    )
    is_statistically_significant: bool = Field(
        default=False,
        description="True if p-value <= significance_level (default 0.05)",
    )
    method: str = Field(
        default="welch_binary_segmentation",
        description="Statistical change-point estimation method applied",
    )
    minimum_segment_size: int = Field(
        default=5,
        description="Minimum consecutive observations required on each side of split",
    )
    observations_used: int = Field(
        ..., description="Total valid observations analyzed in the series"
    )
    pre_change_period: tuple[date, date] | None = Field(
        default=None, description="Date bounds (start, end) of pre-change segment"
    )
    post_change_period: tuple[date, date] | None = Field(
        default=None, description="Date bounds (start, end) of post-change segment"
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic statistics (degrees of freedom, SSE reduction, R^2)",
    )


class ChangePointRequest(BaseModel):
    """Request payload for statistical change-point detection."""

    metric: str = Field(
        default="total_gmv",
        description="Target metric (e.g. total_gmv, orders_count, average_order_value)",
    )
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")
    product_category: str | None = Field(
        default=None, description="Optional product category filter"
    )
    minimum_segment_size: int = Field(
        default=5, ge=2, le=30, description="Minimum observations per partition"
    )
    significance_level: float = Field(
        default=0.05, gt=0.0, lt=0.5, description="Alpha significance threshold"
    )
    variance_ratio_threshold: float = Field(
        default=2.5, gt=1.0, description="Variance ratio threshold for variance shift"
    )
    method: Literal["welch_binary_segmentation", "cusum_likelihood"] = Field(
        default="welch_binary_segmentation",
        description="Statistical change-point estimation algorithm",
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "ChangePointRequest":
        """Ensure end_date is on or after start_date."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ChangePointSeriesResponse(BaseModel):
    """Consolidated change-point analysis response with full time-series."""

    metric: str
    product_category: str | None = None
    start_date: date
    end_date: date
    change_point: ChangePointResult
    time_series: list[DailyKPIObservation]
