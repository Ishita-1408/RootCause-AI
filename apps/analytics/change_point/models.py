"""Pydantic data models for Change-Point and Regime-Shift Detection (Phase L)."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from apps.analytics.anomaly.models import DailyKPIObservation

PersistenceClassification = Literal[
    "SPIKE",
    "TEMPORARY_SHIFT",
    "PERSISTENT_SHIFT",
    "INSUFFICIENT_EVIDENCE",
]

RegimeType = Literal[
    "normal",
    "isolated_anomaly",
    "sustained_level_shift",
    "variance_regime_shift",
    "gradual_trend",
    "insufficient_data",
]

DetectionMethod = Literal[
    "pelt",
    "cusum",
    "rolling_baseline",
    "welch_binary_segmentation",
    "insufficient_data",
]


class ChangePointResult(BaseModel):
    """Statistical change-point and persistent regime-shift evaluation result."""

    metric: str = Field(..., description="Target metric name")
    detected: bool = Field(
        default=False,
        description="True if a reliable structural change point was detected",
    )
    change_point_detected: bool = Field(
        default=False,
        description="Backward-compatible alias for detected",
    )
    change_point_date: date | None = Field(
        default=None,
        description="Date when the structural regime shift occurred",
    )
    pre_change_mean: float | None = Field(
        default=None,
        description="Mean of the segment prior to change point",
    )
    post_change_mean: float | None = Field(
        default=None,
        description="Mean of the segment after change point",
    )
    absolute_shift: float | None = Field(
        default=None,
        description="Absolute difference between post-change and pre-change means",
    )
    relative_shift_pct: float | None = Field(
        default=None,
        description="Percentage shift ((mu2 - mu1) / mu1 * 100)",
    )
    mean_shift_pct: float | None = Field(
        default=None,
        description="Backward-compatible alias for relative_shift_pct",
    )
    persistence: PersistenceClassification = Field(
        default="INSUFFICIENT_EVIDENCE",
        description="Persistence classification tier",
    )
    persistence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of post-break observations maintaining shift direction",
    )
    persistence_days: int = Field(
        default=0,
        ge=0,
        description="Consecutive days the metric stayed in the new regime",
    )
    regime_type: RegimeType = Field(
        default="normal",
        description="Regime classification type",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Statistical confidence in change point detection",
    )
    statistical_score: float | None = Field(
        default=None,
        description="Test statistic magnitude (|t|, CUSUM peak, or PELT cost drop)",
    )
    test_statistic: float | None = Field(
        default=None,
        description="Primary test statistic",
    )
    p_value: float | None = Field(
        default=None,
        description="Two-tailed p-value where applicable",
    )
    is_statistically_significant: bool = Field(
        default=False,
        description="True if p-value <= alpha (0.05)",
    )
    detection_method: DetectionMethod = Field(
        default="pelt",
        description="Method: pelt, cusum, rolling_baseline, welch_binary_segmentation",
    )
    method: str = Field(
        default="pelt",
        description="Backward-compatible alias for detection_method",
    )
    sample_size_before: int | None = Field(
        default=None,
        description="Observations before change point",
    )
    sample_size_after: int | None = Field(
        default=None,
        description="Observations after change point",
    )
    observations_used: int = Field(
        default=0,
        description="Total valid observations analyzed",
    )
    evidence_strength: Literal["strong", "moderate", "weak", "insufficient"] = Field(
        default="moderate",
        description="Quality of evidence supporting the change point",
    )
    pre_change_variance: float | None = Field(
        default=None,
        description="Variance of pre-change segment",
    )
    post_change_variance: float | None = Field(
        default=None,
        description="Variance of post-change segment",
    )
    variance_ratio: float | None = Field(
        default=None,
        description="Variance ratio (s2^2 / s1^2)",
    )
    pre_change_period: tuple[date, date] | None = Field(
        default=None,
        description="Date range of pre-change segment",
    )
    post_change_period: tuple[date, date] | None = Field(
        default=None,
        description="Date range of post-change segment",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Statistical cautions or data constraints",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic statistics (costs, thresholds, BIC/penalty)",
    )

    @model_validator(mode="after")
    def sync_aliases(self) -> "ChangePointResult":
        """Synchronize detected/change_point_detected and method aliases."""
        if self.detected and not self.change_point_detected:
            self.change_point_detected = True
        elif self.change_point_detected and not self.detected:
            self.detected = True

        if self.relative_shift_pct is not None and self.mean_shift_pct is None:
            self.mean_shift_pct = self.relative_shift_pct
        elif self.mean_shift_pct is not None and self.relative_shift_pct is None:
            self.relative_shift_pct = self.mean_shift_pct

        if self.detection_method and not self.method:
            self.method = str(self.detection_method)
        elif self.method and not self.detection_method:
            self.detection_method = self.method  # type: ignore[assignment]
        return self


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
    method: Literal[
        "pelt",
        "cusum",
        "rolling_baseline",
        "welch_binary_segmentation",
        "auto",
    ] = Field(
        default="auto",
        description="Statistical change-point algorithm",
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
