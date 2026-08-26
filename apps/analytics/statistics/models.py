"""Pydantic data models for Statistical Confidence and Significance (Phase K)."""

from typing import Any, Literal

from pydantic import BaseModel, Field

CausalSupportLevel = Literal["descriptive", "associational", "mechanistic", "causal"]
CausalHierarchyLevel = Literal[1, 2, 3, 4, 5]


class ConfidenceInterval(BaseModel):
    """Statistical confidence interval for a numerical point estimate."""

    point_estimate: float = Field(..., description="Estimated parameter value")
    lower_bound: float | None = Field(
        default=None, description="Lower bound of (1 - alpha) confidence interval"
    )
    upper_bound: float | None = Field(
        default=None, description="Upper bound of (1 - alpha) confidence interval"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.5, lt=1.0, description="Confidence level (e.g. 0.95)"
    )
    standard_error: float | None = Field(
        default=None, description="Standard error of point estimate"
    )
    method: Literal[
        "welch_t", "bootstrap", "normal_approx", "wilson_score", "insufficient_data"
    ] = Field(default="welch_t", description="Statistical interval estimation method")
    is_computable: bool = Field(
        default=True,
        description="False if sample size or variance is insufficient to compute CI",
    )


class StatisticalSignificance(BaseModel):
    """Formal hypothesis test and significance result."""

    test_name: str = Field(
        ..., description="Name of statistical test (e.g. Welch's Two-Sample t-test)"
    )
    test_statistic: float | None = Field(
        default=None, description="Calculated test statistic (e.g. t, z, F)"
    )
    p_value: float | None = Field(
        default=None, description="Two-tailed p-value for the hypothesis test"
    )
    degrees_of_freedom: float | None = Field(
        default=None, description="Degrees of freedom where applicable"
    )
    alpha: float = Field(
        default=0.05, gt=0.0, lt=0.5, description="Significance threshold (alpha)"
    )
    is_statistically_significant: bool = Field(
        default=False, description="True if p_value <= alpha"
    )
    hypothesis_null: str = Field(
        default="No difference between distributions (H0: mu1 = mu2)",
        description="Null hypothesis statement",
    )
    hypothesis_alternative: str = Field(
        default="Significant shift between distributions (H1: mu1 != mu2)",
        description="Alternative hypothesis statement",
    )


class StatisticalEstimate(BaseModel):
    """Complete statistical estimate with uncertainty and significance evaluation."""

    metric_name: str
    estimate_type: str = Field(
        ...,
        description="Type of estimate: mean_shift, absolute_change, slice_contribution",
    )
    point_estimate: float
    confidence_interval: ConfidenceInterval
    significance: StatisticalSignificance | None = None
    effect_size: float | None = Field(
        default=None, description="Standardized or percentage effect size"
    )
    effect_size_type: str | None = Field(
        default=None, description="Type: relative_pct, cohens_d, percentage_points"
    )
    sample_size: int | None = Field(
        default=None, description="Effective sample size (n)"
    )
    practical_significance: (
        Literal["negligible", "moderate", "substantial", "critical"] | None
    ) = Field(default=None, description="Practical magnitude interpretation")
    causal_support_level: CausalSupportLevel = Field(
        default="associational",
        description=(
            "Degree of causal identification: descriptive, "
            "associational, mechanistic, or causal"
        ),
    )
    causal_hierarchy_level: CausalHierarchyLevel = Field(
        default=3,
        description="Causal hierarchy level 1 to 5",
    )
    details: dict[str, Any] = Field(default_factory=dict)


class TemporalStatisticalEvidence(BaseModel):
    """Statistical evidence regarding time-series regime shifts and anomaly validity."""

    metric: str
    anomaly_date_estimate: StatisticalEstimate | None = None
    change_point_detected: bool = False
    regime_type: str = "normal"
    pre_change_mean: float | None = None
    post_change_mean: float | None = None
    mean_shift_estimate: StatisticalEstimate | None = None
    p_value: float | None = None
    is_statistically_significant: bool = False


class DriverStatisticalEvidence(BaseModel):
    """Statistical evidence regarding driver decompositions (Volume vs AOV, Slices)."""

    volume_effect_estimate: StatisticalEstimate | None = None
    aov_effect_estimate: StatisticalEstimate | None = None
    operational_effect_estimate: StatisticalEstimate | None = None
    top_slice_estimates: list[StatisticalEstimate] = Field(default_factory=list)


class StatisticalEvidenceSummary(BaseModel):
    """Consolidated statistical credibility payload attached to investigation."""

    temporal_evidence: TemporalStatisticalEvidence
    driver_evidence: DriverStatisticalEvidence
    causal_support_level: CausalSupportLevel = Field(
        default="mechanistic",
        description="Primary investigation causal support tier (default mechanistic)",
    )
    methodology_notes: list[str] = Field(
        default_factory=lambda: [
            "Estimates use two-sample Welch t-intervals (95% confidence).",
            "p < 0.05 indicates statistical association, NOT causal proof.",
            "Decompositions are deterministic accounting identities over marts.",
        ]
    )
