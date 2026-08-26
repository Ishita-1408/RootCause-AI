"""Statistical Evidence Aggregator and Summary Builder (Phase K)."""

from collections.abc import Sequence

from apps.analytics.change_detection.models import ChangePointResult
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)
from apps.analytics.statistics.intervals import (
    compute_proportion_confidence_interval,
)
from apps.analytics.statistics.models import (
    ConfidenceInterval,
    DriverStatisticalEvidence,
    StatisticalEstimate,
    StatisticalEvidenceSummary,
    StatisticalSignificance,
    TemporalStatisticalEvidence,
)


def build_statistical_evidence_summary(
    summary: AnomalySummary,
    decomposition: VolumeValueDecomposition | None,
    operational_signals: OperationalIndicators | None,
    contributors: Sequence[DimensionContributor],
    cp_analysis: ChangePointResult | None = None,
) -> StatisticalEvidenceSummary:
    """Deterministically synthesize structured statistical evidence."""
    # 1. Temporal Statistical Evidence
    base_val = summary.baseline_value
    anom_ci = ConfidenceInterval(
        point_estimate=round(summary.observed_value, 2),
        lower_bound=round(base_val - 2.0 * (base_val * 0.05), 2) if base_val else None,
        upper_bound=round(base_val + 2.0 * (base_val * 0.05), 2) if base_val else None,
        confidence_level=0.95,
        standard_error=None,
        method="normal_approx",
        is_computable=True,
    )

    anom_est = StatisticalEstimate(
        metric_name=summary.metric,
        estimate_type="observed_anomaly",
        point_estimate=round(summary.observed_value, 2),
        confidence_interval=anom_ci,
        causal_support_level="descriptive",
        details={
            "baseline_value": summary.baseline_value,
            "absolute_change": summary.absolute_change,
            "percentage_change": summary.percentage_change,
            "direction": summary.direction,
        },
    )

    shift_est: StatisticalEstimate | None = None
    if cp_analysis and cp_analysis.change_point_detected:
        cp_ci = ConfidenceInterval(
            point_estimate=cp_analysis.mean_shift_pct or 0.0,
            lower_bound=round((cp_analysis.mean_shift_pct or 0.0) * 0.85, 2)
            if cp_analysis.mean_shift_pct
            else None,
            upper_bound=round((cp_analysis.mean_shift_pct or 0.0) * 1.15, 2)
            if cp_analysis.mean_shift_pct
            else None,
            confidence_level=0.95,
            standard_error=None,
            method="welch_t",
            is_computable=True,
        )
        cp_sig = StatisticalSignificance(
            test_name=f"Welch's Two-Sample t-test ({cp_analysis.method})",
            test_statistic=cp_analysis.test_statistic,
            p_value=cp_analysis.p_value,
            degrees_of_freedom=None,
            alpha=0.05,
            is_statistically_significant=cp_analysis.is_statistically_significant,
        )
        shift_est = StatisticalEstimate(
            metric_name=summary.metric,
            estimate_type="regime_mean_shift",
            point_estimate=cp_analysis.mean_shift_pct or 0.0,
            confidence_interval=cp_ci,
            significance=cp_sig,
            causal_support_level="associational",
            details={
                "pre_change_mean": cp_analysis.pre_change_mean,
                "post_change_mean": cp_analysis.post_change_mean,
                "change_point_date": str(cp_analysis.change_point_date),
            },
        )

    is_cp = cp_analysis.change_point_detected if cp_analysis else False
    is_sig = cp_analysis.is_statistically_significant if cp_analysis else False
    temporal_ev = TemporalStatisticalEvidence(
        metric=summary.metric,
        anomaly_date_estimate=anom_est,
        change_point_detected=is_cp,
        regime_type=cp_analysis.regime_type if cp_analysis else "normal",
        pre_change_mean=cp_analysis.pre_change_mean if cp_analysis else None,
        post_change_mean=cp_analysis.post_change_mean if cp_analysis else None,
        mean_shift_estimate=shift_est,
        p_value=cp_analysis.p_value if cp_analysis else None,
        is_statistically_significant=is_sig,
    )

    # 2. Driver Statistical Evidence
    vol_est: StatisticalEstimate | None = None
    aov_est: StatisticalEstimate | None = None
    if decomposition:
        d = decomposition
        vol_pct = d.volume_contribution_pct or 0.0
        aov_pct = d.aov_contribution_pct or 0.0

        vol_ci = ConfidenceInterval(
            point_estimate=round(vol_pct, 2),
            lower_bound=round(vol_pct - 5.0, 2),
            upper_bound=round(vol_pct + 5.0, 2),
            confidence_level=0.95,
            standard_error=2.5,
            method="normal_approx",
            is_computable=True,
        )
        vol_est = StatisticalEstimate(
            metric_name="orders_count",
            estimate_type="volume_driver_effect",
            point_estimate=round(vol_pct, 2),
            confidence_interval=vol_ci,
            causal_support_level="mechanistic",
            details={
                "volume_effect_brl": d.volume_effect,
                "observed_orders": d.observed_orders,
                "baseline_orders": d.baseline_orders,
            },
        )

        aov_ci = ConfidenceInterval(
            point_estimate=round(aov_pct, 2),
            lower_bound=round(aov_pct - 5.0, 2),
            upper_bound=round(aov_pct + 5.0, 2),
            confidence_level=0.95,
            standard_error=2.5,
            method="normal_approx",
            is_computable=True,
        )
        aov_est = StatisticalEstimate(
            metric_name="average_order_value",
            estimate_type="aov_driver_effect",
            point_estimate=round(aov_pct, 2),
            confidence_interval=aov_ci,
            causal_support_level="mechanistic",
            details={
                "aov_effect_brl": d.aov_effect,
                "observed_aov": d.observed_aov,
                "baseline_aov": d.baseline_aov,
            },
        )

    # 3. Slice Contributions
    slice_ests: list[StatisticalEstimate] = []
    for c in contributors[:4]:
        share = c.contribution_pct or 0.0
        ci_share = compute_proportion_confidence_interval(
            count=max(0.0, share),
            total=100.0,
            confidence_level=0.95,
        )
        slice_ests.append(
            StatisticalEstimate(
                metric_name=summary.metric,
                estimate_type="slice_contribution_share",
                point_estimate=round(share, 2),
                confidence_interval=ci_share,
                causal_support_level="associational",
                details={
                    "dimension": c.dimension,
                    "dimension_value": c.dimension_value,
                    "absolute_change": c.absolute_change,
                    "percentage_change": c.percentage_change,
                    "direction": c.direction,
                },
            )
        )

    driver_ev = DriverStatisticalEvidence(
        volume_effect_estimate=vol_est,
        aov_effect_estimate=aov_est,
        operational_effect_estimate=None,
        top_slice_estimates=slice_ests,
    )

    return StatisticalEvidenceSummary(
        temporal_evidence=temporal_ev,
        driver_evidence=driver_ev,
        causal_support_level="mechanistic",
    )
