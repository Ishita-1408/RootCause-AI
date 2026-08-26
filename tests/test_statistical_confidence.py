"""Unit and Integration Tests for Statistical Confidence and Significance (Phase K)."""

import math
from datetime import date

from apps.analytics.change_detection.models import ChangePointResult
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    VolumeValueDecomposition,
)
from apps.analytics.statistics import (
    build_statistical_evidence_summary,
    compute_bootstrap_confidence_interval,
    compute_mean_confidence_interval,
    compute_proportion_confidence_interval,
    compute_welch_confidence_interval,
    sanitize_causal_language,
    validate_causal_language,
)


def test_mean_confidence_interval_basic() -> None:
    """Test 95% confidence interval on a standard sample."""
    sample = [100.0, 102.0, 98.0, 104.0, 96.0, 101.0, 99.0]
    ci = compute_mean_confidence_interval(sample, confidence_level=0.95)

    assert ci.is_computable is True
    assert ci.point_estimate == 100.0
    assert ci.lower_bound is not None and ci.upper_bound is not None
    assert ci.lower_bound < ci.point_estimate < ci.upper_bound
    assert ci.method == "welch_t"
    assert ci.standard_error is not None and ci.standard_error > 0


def test_mean_confidence_interval_zero_variance() -> None:
    """Test confidence interval when all observations are identical."""
    sample = [50.0, 50.0, 50.0, 50.0]
    ci = compute_mean_confidence_interval(sample, confidence_level=0.95)

    assert ci.is_computable is True
    assert ci.point_estimate == 50.0
    assert ci.lower_bound == 50.0
    assert ci.upper_bound == 50.0
    assert ci.standard_error == 0.0


def test_mean_confidence_interval_insufficient_data() -> None:
    """Test confidence interval when sample size is too small (< 2)."""
    ci_single = compute_mean_confidence_interval([42.0])
    assert ci_single.is_computable is False
    assert ci_single.method == "insufficient_data"
    assert ci_single.lower_bound is None

    ci_empty = compute_mean_confidence_interval([])
    assert ci_empty.is_computable is False
    assert ci_empty.point_estimate == 0.0


def test_welch_confidence_interval_and_significance() -> None:
    """Test two-sample Welch t-interval and p-value on shifted distributions."""
    s1 = [10.0, 11.0, 12.0, 10.5, 11.5]
    s2 = [25.0, 26.0, 24.5, 25.5, 27.0]

    ci, sig = compute_welch_confidence_interval(
        s1, s2, confidence_level=0.95, alpha=0.05
    )

    assert ci.is_computable is True
    assert ci.point_estimate > 0  # mu2 > mu1
    assert ci.lower_bound is not None and ci.upper_bound is not None
    assert ci.lower_bound < ci.point_estimate < ci.upper_bound

    assert sig.is_statistically_significant is True
    assert sig.p_value is not None and sig.p_value < 0.001
    assert sig.test_statistic is not None and sig.test_statistic > 0
    assert sig.degrees_of_freedom is not None and sig.degrees_of_freedom > 0


def test_welch_insufficient_samples() -> None:
    """Test Welch t-interval when one or both samples are insufficient."""
    ci, sig = compute_welch_confidence_interval([10.0], [20.0, 21.0])
    assert ci.is_computable is False
    assert ci.method == "insufficient_data"
    assert sig.is_statistically_significant is False
    assert sig.p_value is None


def test_proportion_confidence_interval_wilson() -> None:
    """Test Wilson score interval for share / proportion."""
    ci = compute_proportion_confidence_interval(count=30.0, total=100.0)
    assert ci.is_computable is True
    assert ci.point_estimate == 0.30
    assert ci.lower_bound is not None and ci.upper_bound is not None
    assert 0.0 <= ci.lower_bound < 0.30 < ci.upper_bound <= 1.0
    assert ci.method == "wilson_score"


def test_proportion_confidence_interval_bounds() -> None:
    """Test Wilson score interval edge cases at 0% and 100%."""
    ci_zero = compute_proportion_confidence_interval(count=0.0, total=50.0)
    assert ci_zero.is_computable is True
    assert ci_zero.point_estimate == 0.0
    assert ci_zero.lower_bound == 0.0
    assert ci_zero.upper_bound is not None and ci_zero.upper_bound > 0.0

    ci_invalid = compute_proportion_confidence_interval(count=10.0, total=0.0)
    assert ci_invalid.is_computable is False
    assert ci_invalid.method == "insufficient_data"


def test_bootstrap_confidence_interval() -> None:
    """Test non-parametric bootstrap interval estimation."""
    sample = [10.0, 12.0, 15.0, 11.0, 14.0, 13.0, 16.0]
    ci = compute_bootstrap_confidence_interval(
        sample,
        statistic_fn=lambda arr: float(math.fsum(arr) / len(arr)),
        n_resamples=200,
        random_seed=42,
    )
    assert ci.is_computable is True
    assert ci.method == "bootstrap"
    assert ci.lower_bound is not None and ci.upper_bound is not None
    assert ci.lower_bound <= ci.point_estimate <= ci.upper_bound


def test_causal_language_guardrails_validation() -> None:
    """Test rejection of causal claims and acceptance of associational phrasing."""
    # Forbidden causal phrasing
    assert (
        validate_causal_language(
            "São Paulo caused the revenue decline.", "associational"
        )[0]
        is False
    )
    assert (
        validate_causal_language("AOV directly caused the drop.", "mechanistic")[0]
        is False
    )
    assert (
        validate_causal_language(
            "Carrier delay is responsible for the loss.", "associational"
        )[0]
        is False
    )
    assert (
        validate_causal_language("The regression proves causality.", "associational")[0]
        is False
    )

    # Allowed under 'causal' support tier (e.g. experimental randomized trial)
    assert (
        validate_causal_language(
            "Pricing experiment caused higher conversion.", "causal"
        )[0]
        is True
    )

    # Allowed associational & mechanistic phrasing
    assert (
        validate_causal_language(
            "Revenue growth is concentrated in São Paulo.", "associational"
        )[0]
        is True
    )
    assert (
        validate_causal_language(
            "Order volume is the strongest supported driver.", "mechanistic"
        )[0]
        is True
    )
    assert (
        validate_causal_language(
            "Basket pricing explains 45% of observed variance.", "mechanistic"
        )[0]
        is True
    )


def test_causal_language_sanitization() -> None:
    """Test deterministic replacement of forbidden causal verbs."""
    text = "São Paulo caused the revenue decline and directly caused lower orders."
    sanitized = sanitize_causal_language(text)
    assert "caused" not in sanitized
    assert "associated with" in sanitized
    assert "strongest supported driver" in sanitized


def test_build_statistical_evidence_summary() -> None:
    """Test synthesizing a complete statistical evidence summary."""
    summary = AnomalySummary(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        observed_value=150000.0,
        baseline_value=30000.0,
        absolute_change=120000.0,
        percentage_change=400.0,
        direction="increase",
        baseline_start_date=date(2017, 11, 17),
        baseline_end_date=date(2017, 11, 23),
    )
    decomp = VolumeValueDecomposition(
        observed_orders=1000.0,
        baseline_orders=200.0,
        observed_aov=150.0,
        baseline_aov=150.0,
        volume_effect=120000.0,
        aov_effect=0.0,
        interaction_effect=0.0,
        volume_contribution_pct=100.0,
        aov_contribution_pct=0.0,
        interaction_contribution_pct=0.0,
        total_change=120000.0,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=60000.0,
            baseline_value=10000.0,
            absolute_change=50000.0,
            percentage_change=500.0,
            contribution_pct=41.67,
            direction="increase",
            rank=1,
        )
    ]
    cp = ChangePointResult(
        metric="total_gmv",
        change_point_detected=True,
        change_point_date=date(2017, 11, 24),
        regime_type="sustained_level_shift",
        pre_change_mean=30000.0,
        post_change_mean=150000.0,
        mean_shift_pct=400.0,
        pre_change_variance=5000.0,
        post_change_variance=8000.0,
        variance_ratio=1.6,
        test_statistic=8.5,
        p_value=0.00001,
        is_statistically_significant=True,
        method="welch_binary_segmentation",
        minimum_segment_size=3,
        observations_used=14,
    )

    stat_summary = build_statistical_evidence_summary(
        summary=summary,
        decomposition=decomp,
        operational_signals=None,
        contributors=contributors,
        cp_analysis=cp,
    )

    assert stat_summary.causal_support_level == "mechanistic"
    assert stat_summary.temporal_evidence.change_point_detected is True
    assert stat_summary.temporal_evidence.is_statistically_significant is True
    assert stat_summary.driver_evidence.volume_effect_estimate is not None
    assert stat_summary.driver_evidence.volume_effect_estimate.point_estimate == 100.0
    assert len(stat_summary.driver_evidence.top_slice_estimates) == 1
    assert stat_summary.driver_evidence.top_slice_estimates[0].point_estimate == 41.67


def test_effect_size_and_practical_significance() -> None:
    """Test effect size evaluation and practical significance thresholding."""
    from apps.analytics.statistics.models import StatisticalEstimate

    # Large practical effect
    large_est = StatisticalEstimate(
        metric_name="total_gmv",
        estimate_type="mean_shift",
        point_estimate=400.0,
        confidence_interval=compute_mean_confidence_interval([380.0, 410.0, 400.0]),
        effect_size=0.85,
        effect_size_type="relative_pct",
        practical_significance="critical",
        causal_support_level="associational",
        causal_hierarchy_level=2,
    )
    assert large_est.practical_significance == "critical"
    assert large_est.causal_hierarchy_level == 2

    # Negligible effect size
    negligible_est = StatisticalEstimate(
        metric_name="total_gmv",
        estimate_type="slice_contribution",
        point_estimate=0.005,
        confidence_interval=compute_proportion_confidence_interval(0.005, 100.0),
        effect_size=0.0001,
        effect_size_type="percentage_points",
        practical_significance="negligible",
        causal_support_level="associational",
        causal_hierarchy_level=2,
    )
    assert negligible_est.practical_significance == "negligible"


def test_causal_hierarchy_five_level_mapping() -> None:
    """Test the 5 distinct causal hierarchy levels."""
    # Level 1: Observed anomaly (descriptive)
    valid_l1, _ = validate_causal_language("GMV rose to R$ 150,000", "descriptive")
    assert valid_l1 is True

    # Level 2: Statistical association
    valid_l2, _ = validate_causal_language(
        "Volume is associated with GMV shift", "associational"
    )
    assert valid_l2 is True

    # Level 3: Contribution / decomposition
    valid_l3, _ = validate_causal_language(
        "Volume is the strongest supported driver", "mechanistic"
    )
    assert valid_l3 is True

    # Level 4: Operational corroboration
    valid_l4, _ = validate_causal_language(
        "Consistent with carrier SLA degradation", "mechanistic"
    )
    assert valid_l4 is True

    # Level 5: Experimental Causal identification
    valid_l5, _ = validate_causal_language(
        "Pricing experiment caused conversion increase", "causal"
    )
    assert valid_l5 is True

    # Observational attempt at Level 5 phrasing must fail
    invalid_obs, err = validate_causal_language(
        "Pricing caused conversion increase", "mechanistic"
    )
    assert invalid_obs is False
    assert "Unsupported causal language" in (err or "")
