"""Deterministic Statistical Change-Point Detectors for RootCause AI (Phase L)."""

import math
from collections.abc import Sequence
from datetime import date

import numpy as np

from apps.analytics.anomaly.models import DailyKPIObservation
from apps.analytics.change_detection.detector import student_t_pvalue
from apps.analytics.change_point.models import ChangePointResult
from apps.analytics.change_point.scoring import (
    evaluate_persistence,
    select_detection_method,
)


def _extract_clean_series(
    observations: Sequence[DailyKPIObservation],
) -> tuple[list[date], list[float]]:
    """Sort and extract dates and valid numerical values from observations."""
    sorted_obs = sorted(observations, key=lambda x: x.date)
    dates: list[date] = []
    values: list[float] = []
    for o in sorted_obs:
        if o.value is not None and not math.isnan(o.value):
            dates.append(o.date)
            values.append(float(o.value))
    return dates, values


def detect_cusum_change_point(
    dates: Sequence[date],
    values: Sequence[float],
    metric: str = "total_gmv",
    significance_level: float = 0.05,
    minimum_segment_size: int = 3,
) -> ChangePointResult:
    """CUSUM detector for sustained mean shifts."""
    n = len(values)
    if n < minimum_segment_size * 2:
        return ChangePointResult(
            metric=metric,
            detected=False,
            persistence="INSUFFICIENT_EVIDENCE",
            regime_type="insufficient_data",
            detection_method="cusum",
            observations_used=n,
            limitations=["Insufficient sample size for CUSUM evaluation (n < 6)."],
        )

    arr = np.array(values, dtype=float)
    overall_mean = float(np.mean(arr))
    overall_std = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    if overall_std < 1e-9:
        return ChangePointResult(
            metric=metric,
            detected=False,
            pre_change_mean=overall_mean,
            post_change_mean=overall_mean,
            absolute_shift=0.0,
            relative_shift_pct=0.0,
            persistence="INSUFFICIENT_EVIDENCE",
            regime_type="normal",
            detection_method="cusum",
            observations_used=n,
            limitations=["Zero variance series — no shift detectable."],
        )

    deviations = arr - overall_mean
    cusum_curve = np.cumsum(deviations)
    max_idx = int(np.argmax(np.abs(cusum_curve)))
    peak_val = float(np.abs(cusum_curve[max_idx]))

    split_idx = max(minimum_segment_size, min(max_idx + 1, n - minimum_segment_size))

    s1, s2 = arr[:split_idx], arr[split_idx:]
    mu1, mu2 = float(np.mean(s1)), float(np.mean(s2))
    var1 = float(np.var(s1, ddof=1)) if len(s1) > 1 else 0.0
    var2 = float(np.var(s2, ddof=1)) if len(s2) > 1 else 0.0
    n1, n2 = len(s1), len(s2)

    se_diff = math.sqrt((var1 / n1) + (var2 / n2)) if (var1 + var2) > 0 else 1e-9
    diff = mu2 - mu1
    t_stat = diff / se_diff

    num_df = ((var1 / n1) + (var2 / n2)) ** 2
    den_df = (((var1 / n1) ** 2) / max(n1 - 1, 1)) + (
        ((var2 / n2) ** 2) / max(n2 - 1, 1)
    )
    df_val = num_df / den_df if den_df > 0 else float(n1 + n2 - 2)

    p_val = student_t_pvalue(abs(t_stat), df_val)
    is_sig = bool(p_val <= significance_level and abs(diff) > 1e-4)
    rel_pct = round((diff / mu1) * 100.0, 2) if abs(mu1) > 1e-9 else 0.0

    h_boundary = 1.25 * overall_std * math.sqrt(n)
    is_cusum_detected = peak_val >= h_boundary and is_sig

    p_class, p_score, p_days, r_type = evaluate_persistence(
        values=values,
        change_idx=split_idx if is_cusum_detected else None,
        pre_mean=mu1 if is_cusum_detected else None,
        post_mean=mu2 if is_cusum_detected else None,
        is_significant=is_cusum_detected,
    )

    return ChangePointResult(
        metric=metric,
        detected=is_cusum_detected,
        change_point_date=dates[split_idx] if is_cusum_detected else None,
        pre_change_mean=round(mu1, 4),
        post_change_mean=round(mu2, 4),
        absolute_shift=round(diff, 4),
        relative_shift_pct=rel_pct,
        persistence=p_class,
        persistence_score=p_score,
        persistence_days=p_days,
        regime_type=r_type,
        confidence=round(1.0 - min(p_val, 1.0), 4) if is_cusum_detected else 0.0,
        statistical_score=round(peak_val, 4),
        test_statistic=round(t_stat, 4),
        p_value=round(p_val, 6),
        is_statistically_significant=is_sig,
        detection_method="cusum",
        sample_size_before=n1,
        sample_size_after=n2,
        observations_used=n,
        evidence_strength=(
            "strong" if is_cusum_detected and p_val < 0.01 else "moderate"
        ),
        pre_change_variance=round(var1, 4),
        post_change_variance=round(var2, 4),
        pre_change_period=(dates[0], dates[split_idx - 1]),
        post_change_period=(dates[split_idx], dates[-1]),
        details={
            "cusum_peak": peak_val,
            "decision_boundary": h_boundary,
            "degrees_of_freedom": round(df_val, 2),
        },
    )


def detect_pelt_change_point(
    dates: Sequence[date],
    values: Sequence[float],
    metric: str = "total_gmv",
    significance_level: float = 0.05,
    minimum_segment_size: int = 3,
    penalty_multiplier: float = 1.5,
) -> ChangePointResult:
    """PELT algorithm with L2 sum-of-squares cost and BIC penalty."""
    n = len(values)
    if n < minimum_segment_size * 2:
        return detect_cusum_change_point(
            dates, values, metric, significance_level, minimum_segment_size
        )

    arr = np.array(values, dtype=float)
    sample_var = float(np.var(arr, ddof=1)) if n > 1 else 1.0
    if sample_var < 1e-9:
        sample_var = 1.0

    penalty = penalty_multiplier * 2.0 * math.log(max(n, 2)) * sample_var

    def segment_cost(start: int, end: int) -> float:
        if end - start < 1:
            return 0.0
        seg = arr[start:end]
        m = float(np.mean(seg))
        return float(np.sum((seg - m) ** 2))

    base_cost = segment_cost(0, n)
    best_split = None
    min_cost = base_cost

    for k in range(minimum_segment_size, n - minimum_segment_size + 1):
        c1 = segment_cost(0, k)
        c2 = segment_cost(k, n)
        total_cost = c1 + c2 + penalty
        if total_cost < min_cost:
            min_cost = total_cost
            best_split = k

    if best_split is None:
        return detect_welch_binary_segmentation(
            dates, values, metric, significance_level, minimum_segment_size
        )

    split_idx = best_split
    s1, s2 = arr[:split_idx], arr[split_idx:]
    mu1, mu2 = float(np.mean(s1)), float(np.mean(s2))
    var1 = float(np.var(s1, ddof=1)) if len(s1) > 1 else 0.0
    var2 = float(np.var(s2, ddof=1)) if len(s2) > 1 else 0.0
    n1, n2 = len(s1), len(s2)

    se_diff = math.sqrt((var1 / n1) + (var2 / n2)) if (var1 + var2) > 0 else 1e-9
    diff = mu2 - mu1
    t_stat = diff / se_diff

    num_df = ((var1 / n1) + (var2 / n2)) ** 2
    den_df = (((var1 / n1) ** 2) / max(n1 - 1, 1)) + (
        ((var2 / n2) ** 2) / max(n2 - 1, 1)
    )
    df_val = num_df / den_df if den_df > 0 else float(n1 + n2 - 2)

    p_val = student_t_pvalue(abs(t_stat), df_val)
    is_sig = bool(p_val <= significance_level and abs(diff) > 1e-4)

    rel_pct = round((diff / mu1) * 100.0, 2) if abs(mu1) > 1e-9 else 0.0
    cost_reduction = base_cost - (
        segment_cost(0, split_idx) + segment_cost(split_idx, n)
    )

    p_class, p_score, p_days, r_type = evaluate_persistence(
        values=values,
        change_idx=split_idx if is_sig else None,
        pre_mean=mu1 if is_sig else None,
        post_mean=mu2 if is_sig else None,
        is_significant=is_sig,
    )

    return ChangePointResult(
        metric=metric,
        detected=is_sig,
        change_point_date=dates[split_idx] if is_sig else None,
        pre_change_mean=round(mu1, 4),
        post_change_mean=round(mu2, 4),
        absolute_shift=round(diff, 4),
        relative_shift_pct=rel_pct,
        persistence=p_class,
        persistence_score=p_score,
        persistence_days=p_days,
        regime_type=r_type,
        confidence=round(1.0 - min(p_val, 1.0), 4) if is_sig else 0.0,
        statistical_score=round(cost_reduction, 4),
        test_statistic=round(t_stat, 4),
        p_value=round(p_val, 6),
        is_statistically_significant=is_sig,
        detection_method="pelt",
        sample_size_before=n1,
        sample_size_after=n2,
        observations_used=n,
        evidence_strength="strong" if is_sig and p_val < 0.01 else "moderate",
        pre_change_variance=round(var1, 4),
        post_change_variance=round(var2, 4),
        pre_change_period=(dates[0], dates[split_idx - 1]),
        post_change_period=(dates[split_idx], dates[-1]),
        details={
            "pelt_cost_reduction": cost_reduction,
            "penalty": penalty,
            "degrees_of_freedom": round(df_val, 2),
        },
    )


def detect_rolling_baseline(
    dates: Sequence[date],
    values: Sequence[float],
    metric: str = "total_gmv",
    significance_level: float = 0.05,
    minimum_segment_size: int = 2,
) -> ChangePointResult:
    """Transparent rolling baseline detector for short series and local shifts."""
    n = len(values)
    if n < minimum_segment_size * 2:
        return ChangePointResult(
            metric=metric,
            detected=False,
            persistence="INSUFFICIENT_EVIDENCE",
            regime_type="insufficient_data",
            detection_method="rolling_baseline",
            observations_used=n,
            limitations=["Insufficient observations for rolling baseline (n < 4)."],
        )

    arr = np.array(values, dtype=float)
    split_idx = n // 2
    s1, s2 = arr[:split_idx], arr[split_idx:]
    mu1, mu2 = float(np.mean(s1)), float(np.mean(s2))
    var1 = float(np.var(s1, ddof=1)) if len(s1) > 1 else 0.0
    var2 = float(np.var(s2, ddof=1)) if len(s2) > 1 else 0.0
    n1, n2 = len(s1), len(s2)

    diff = mu2 - mu1
    se_diff = math.sqrt((var1 / n1) + (var2 / n2)) if (var1 + var2) > 0 else 1e-9
    t_stat = diff / se_diff
    df_val = float(n1 + n2 - 2)
    p_val = student_t_pvalue(abs(t_stat), df_val)

    is_sig = bool(p_val <= significance_level and abs(diff) > 1e-4)
    rel_pct = round((diff / mu1) * 100.0, 2) if abs(mu1) > 1e-9 else 0.0

    p_class, p_score, p_days, r_type = evaluate_persistence(
        values=values,
        change_idx=split_idx if is_sig else None,
        pre_mean=mu1 if is_sig else None,
        post_mean=mu2 if is_sig else None,
        is_significant=is_sig,
    )

    return ChangePointResult(
        metric=metric,
        detected=is_sig,
        change_point_date=dates[split_idx] if is_sig else None,
        pre_change_mean=round(mu1, 4),
        post_change_mean=round(mu2, 4),
        absolute_shift=round(diff, 4),
        relative_shift_pct=rel_pct,
        persistence=p_class,
        persistence_score=p_score,
        persistence_days=p_days,
        regime_type=r_type,
        confidence=round(1.0 - min(p_val, 1.0), 4) if is_sig else 0.0,
        statistical_score=round(abs(t_stat), 4),
        test_statistic=round(t_stat, 4),
        p_value=round(p_val, 6),
        is_statistically_significant=is_sig,
        detection_method="rolling_baseline",
        sample_size_before=n1,
        sample_size_after=n2,
        observations_used=n,
        evidence_strength="moderate" if is_sig else "weak",
        pre_change_variance=round(var1, 4),
        post_change_variance=round(var2, 4),
        pre_change_period=(dates[0], dates[split_idx - 1]),
        post_change_period=(dates[split_idx], dates[-1]),
    )


def detect_welch_binary_segmentation(
    dates: Sequence[date],
    values: Sequence[float],
    metric: str = "total_gmv",
    significance_level: float = 0.05,
    minimum_segment_size: int = 3,
) -> ChangePointResult:
    """Welch binary segmentation evaluating maximal t-statistic split."""
    from apps.analytics.change_detection.detector import detect_change_point

    obs = [
        DailyKPIObservation(date=d, metric=metric, value=v)
        for d, v in zip(dates, values, strict=False)
    ]
    legacy_res = detect_change_point(
        observations=obs,
        minimum_segment_size=minimum_segment_size,
        significance_level=significance_level,
    )

    change_idx = (
        dates.index(legacy_res.change_point_date)
        if legacy_res.change_point_date and legacy_res.change_point_date in dates
        else None
    )

    p_class, p_score, p_days, r_type = evaluate_persistence(
        values=values,
        change_idx=change_idx,
        pre_mean=legacy_res.pre_change_mean,
        post_mean=legacy_res.post_change_mean,
        is_significant=legacy_res.change_point_detected,
    )

    return ChangePointResult(
        metric=metric,
        detected=legacy_res.change_point_detected,
        change_point_date=legacy_res.change_point_date,
        pre_change_mean=legacy_res.pre_change_mean,
        post_change_mean=legacy_res.post_change_mean,
        absolute_shift=(
            (legacy_res.post_change_mean - legacy_res.pre_change_mean)
            if legacy_res.post_change_mean is not None
            and legacy_res.pre_change_mean is not None
            else None
        ),
        relative_shift_pct=legacy_res.mean_shift_pct,
        persistence=p_class,
        persistence_score=p_score,
        persistence_days=p_days,
        regime_type=r_type,
        confidence=(
            round(1.0 - (legacy_res.p_value or 1.0), 4)
            if legacy_res.change_point_detected
            else 0.0
        ),
        statistical_score=legacy_res.statistical_score,
        test_statistic=legacy_res.test_statistic,
        p_value=legacy_res.p_value,
        is_statistically_significant=legacy_res.is_statistically_significant,
        detection_method="welch_binary_segmentation",
        sample_size_before=legacy_res.details.get("n1"),
        sample_size_after=legacy_res.details.get("n2"),
        observations_used=legacy_res.observations_used,
        evidence_strength="strong" if legacy_res.change_point_detected else "moderate",
        pre_change_variance=legacy_res.pre_change_variance,
        post_change_variance=legacy_res.post_change_variance,
        variance_ratio=legacy_res.variance_ratio,
        pre_change_period=legacy_res.pre_change_period,
        post_change_period=legacy_res.post_change_period,
        details=legacy_res.details,
    )


def run_change_point_analysis(
    observations: Sequence[DailyKPIObservation],
    metric: str = "total_gmv",
    method: str = "auto",
    significance_level: float = 0.05,
    minimum_segment_size: int = 3,
) -> ChangePointResult:
    """Orchestrate deterministic change-point detection across methods."""
    dates, values = _extract_clean_series(observations)
    n = len(values)

    selected_method = select_detection_method(n, method)

    if selected_method == "insufficient_data" or n < minimum_segment_size * 2:
        return ChangePointResult(
            metric=metric,
            detected=False,
            persistence="INSUFFICIENT_EVIDENCE",
            regime_type="insufficient_data",
            detection_method="insufficient_data",
            observations_used=n,
            limitations=[
                f"Sample size ({n}) is insufficient for structural break detection."
            ],
        )

    if selected_method == "pelt":
        return detect_pelt_change_point(
            dates=dates,
            values=values,
            metric=metric,
            significance_level=significance_level,
            minimum_segment_size=minimum_segment_size,
        )
    elif selected_method == "cusum":
        return detect_cusum_change_point(
            dates=dates,
            values=values,
            metric=metric,
            significance_level=significance_level,
            minimum_segment_size=minimum_segment_size,
        )
    elif selected_method == "rolling_baseline":
        return detect_rolling_baseline(
            dates=dates,
            values=values,
            metric=metric,
            significance_level=significance_level,
            minimum_segment_size=minimum_segment_size,
        )
    else:
        return detect_welch_binary_segmentation(
            dates=dates,
            values=values,
            metric=metric,
            significance_level=significance_level,
            minimum_segment_size=minimum_segment_size,
        )
