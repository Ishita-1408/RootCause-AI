"""Statistical Change-Point Detection Engine for RootCause AI (Phase J).

Implements Welch's Binary Segmentation, Robust Outlier Screening,
and BIC-Penalized Linear vs. Step-Function Model Selection to detect
and distinguish:
1. Normal fluctuation
2. Isolated anomaly (spike/dip)
3. Sustained level shift (mean regime change)
4. Variance regime shift (volatility expansion)
5. Gradual linear trend
6. Insufficient data
"""

import math
from datetime import date

import numpy as np
import pandas as pd
import psycopg

from apps.analytics.anomaly.models import DailyKPIObservation
from apps.analytics.anomaly.queries import fetch_daily_kpi_series
from apps.analytics.change_detection.models import (
    ChangePointResult,
    ChangePointSeriesResponse,
    RegimeType,
)


def _betacf(a: float, b: float, x: float) -> float:
    """Evaluate continued fraction for incomplete beta function."""
    maxit = 100
    eps = 3.0e-7
    fpmin = 1.0e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        del_val = d * c
        h *= del_val
        if abs(del_val - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Compute regularized incomplete beta function I_x(a, b)."""
    if x < 0.0 or x > 1.0:
        return 0.0
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    else:
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def student_t_pvalue(t_stat: float, df: float) -> float:
    """Compute two-tailed p-value for Student's t distribution with df."""
    if df <= 0.0:
        return 1.0
    t2 = t_stat * t_stat
    x = df / (df + t2)
    p = _betai(0.5 * df, 0.5, x)
    return max(min(p, 1.0), 0.0)


def detect_change_point(
    observations: list[DailyKPIObservation],
    minimum_segment_size: int = 4,
    significance_level: float = 0.05,
    variance_ratio_threshold: float = 2.5,
    method: str = "welch_binary_segmentation",
) -> ChangePointResult:
    """Detect statistical change points and classify regime dynamics."""
    if not observations:
        return ChangePointResult(
            metric="unknown",
            change_point_detected=False,
            regime_type="insufficient_data",
            observations_used=0,
            minimum_segment_size=minimum_segment_size,
            method=method,
        )

    metric_name = observations[0].metric

    # Clean and sort observations (drop missing / null values)
    df = (
        pd.DataFrame([{"date": o.date, "value": o.value} for o in observations])
        .dropna(subset=["value"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    n_obs = len(df)
    min_required = 2 * minimum_segment_size

    # Guard 1: Insufficient data
    if n_obs < min_required:
        return ChangePointResult(
            metric=metric_name,
            change_point_detected=False,
            regime_type="insufficient_data",
            observations_used=n_obs,
            minimum_segment_size=minimum_segment_size,
            method=method,
            details={
                "reason": (f"Observations ({n_obs}) < 2 * min_segment ({min_required})")
            },
        )

    dates: list[date] = df["date"].tolist()
    values: np.ndarray = df["value"].to_numpy(dtype=float)

    total_var = float(np.var(values, ddof=1)) if n_obs > 1 else 0.0
    mean_all = float(np.mean(values))

    # Guard 2: Constant series with zero variance
    if total_var < 1e-12:
        return ChangePointResult(
            metric=metric_name,
            change_point_detected=False,
            regime_type="normal",
            observations_used=n_obs,
            minimum_segment_size=minimum_segment_size,
            pre_change_mean=round(float(values[0]), 4),
            post_change_mean=round(float(values[0]), 4),
            mean_shift_pct=0.0,
            pre_change_variance=0.0,
            post_change_variance=0.0,
            variance_ratio=1.0,
            statistical_score=0.0,
            method=method,
            details={"reason": "Constant series with zero variance."},
        )

    # 1. Linear Model Fit (Testing for Continuous Gradual Trend)
    x_idx = np.arange(n_obs, dtype=float)
    x_mean = float(np.mean(x_idx))
    ss_xx = float(np.sum((x_idx - x_mean) ** 2))
    ss_xy = float(np.sum((x_idx - x_mean) * (values - mean_all)))
    slope = ss_xy / ss_xx if ss_xx > 0 else 0.0
    intercept = mean_all - slope * x_mean
    y_pred_linear = slope * x_idx + intercept
    ss_tot = float(np.sum((values - mean_all) ** 2))
    ss_res_linear = float(np.sum((values - y_pred_linear) ** 2))
    r2_linear = 1.0 - (ss_res_linear / ss_tot) if ss_tot > 0 else 0.0
    bic_linear = n_obs * math.log(max(ss_res_linear / n_obs, 1e-12)) + 2.0 * math.log(
        n_obs
    )

    # 2. Robust Outlier Screening (Testing for Single Isolated Spike)
    med_val = float(np.median(values))
    mad_val = float(np.median(np.abs(values - med_val)))
    robust_scale = 1.4826 * mad_val if mad_val > 1e-9 else float(np.std(values)) + 1e-6
    robust_z_scores = np.abs(values - med_val) / robust_scale
    max_rz_idx = int(np.argmax(robust_z_scores))
    max_rz = float(robust_z_scores[max_rz_idx])

    is_isolated_spike = False
    if max_rz >= 4.0:
        # Evaluate series with the single outlier point removed
        cleaned_vals = np.delete(values, max_rz_idx)
        n_clean = len(cleaned_vals)
        if n_clean >= min_required:
            mid = n_clean // 2
            c_s1 = cleaned_vals[:mid]
            c_s2 = cleaned_vals[mid:]
            c_var1 = float(np.var(c_s1, ddof=1)) if len(c_s1) > 1 else 0.0
            c_var2 = float(np.var(c_s2, ddof=1)) if len(c_s2) > 1 else 0.0
            c_mu1 = float(np.mean(c_s1))
            c_mu2 = float(np.mean(c_s2))
            c_shift_pct = (
                abs((c_mu2 - c_mu1) / c_mu1) * 100.0 if abs(c_mu1) > 1e-6 else 0.0
            )
            # If the underlying series without the spike is stable in mean and variance
            if (
                c_shift_pct < 10.0
                and max(c_var1, c_var2) / max(min(c_var1, c_var2), 1e-6) < 3.0
            ):
                is_isolated_spike = True

    # 3. Piecewise Constant Step Model (Welch Binary Segmentation)
    best_tau: int | None = None
    best_score = -1.0
    best_t_stat = 0.0
    best_df = 1.0
    best_p_val = 1.0
    best_mu1 = mean_all
    best_mu2 = mean_all
    best_var1 = total_var
    best_var2 = total_var
    best_var_ratio = 1.0
    best_sse_step = ss_tot

    for tau in range(minimum_segment_size, n_obs - minimum_segment_size + 1):
        seg1 = values[:tau]
        seg2 = values[tau:]

        n1 = len(seg1)
        n2 = len(seg2)

        mu1 = float(np.mean(seg1))
        mu2 = float(np.mean(seg2))

        var1 = float(np.var(seg1, ddof=1)) if n1 > 1 else 0.0
        var2 = float(np.var(seg2, ddof=1)) if n2 > 1 else 0.0

        sse_1 = float(np.sum((seg1 - mu1) ** 2))
        sse_2 = float(np.sum((seg2 - mu2) ** 2))
        total_sse = sse_1 + sse_2

        # Between-segment variance reduction
        delta_sse = (n1 * n2 / (n1 + n2)) * ((mu1 - mu2) ** 2)

        se_diff = (
            math.sqrt((var1 / n1) + (var2 / n2)) if (var1 > 0 or var2 > 0) else 1e-6
        )
        t_stat = (mu2 - mu1) / se_diff if se_diff > 0 else 0.0

        num_df = ((var1 / n1) + (var2 / n2)) ** 2
        den_df = (((var1 / n1) ** 2) / max(n1 - 1, 1)) + (
            ((var2 / n2) ** 2) / max(n2 - 1, 1)
        )
        df_val = num_df / den_df if den_df > 0 else float(n1 + n2 - 2)

        p_val = student_t_pvalue(abs(t_stat), df_val)

        if delta_sse > best_score:
            best_score = delta_sse
            best_tau = tau
            best_t_stat = t_stat
            best_df = df_val
            best_p_val = p_val
            best_mu1 = mu1
            best_mu2 = mu2
            best_var1 = var1
            best_var2 = var2
            best_sse_step = total_sse
            min_v = min(var1, var2)
            max_v = max(var1, var2)
            best_var_ratio = (max_v / (min_v + 1e-12)) if min_v > 0 else (max_v + 1.0)

    bic_step = n_obs * math.log(max(best_sse_step / n_obs, 1e-12)) + 3.0 * math.log(
        n_obs
    )

    if best_tau is None:
        return ChangePointResult(
            metric=metric_name,
            change_point_detected=False,
            regime_type="normal",
            observations_used=n_obs,
            minimum_segment_size=minimum_segment_size,
            method=method,
        )

    shift_pct = (
        ((best_mu2 - best_mu1) / abs(best_mu1)) * 100.0 if abs(best_mu1) > 1e-9 else 0.0
    )

    change_date = dates[best_tau]
    pre_period = (dates[0], dates[best_tau - 1])
    post_period = (dates[best_tau], dates[-1])

    is_sig = best_p_val <= significance_level
    is_meaningful_shift = abs(shift_pct) >= 10.0 or abs(best_t_stat) >= 2.5

    # 4. Statistical Regime Classification
    regime: RegimeType = "normal"
    detected = False

    if is_isolated_spike:
        regime = "isolated_anomaly"
        detected = False
    elif r2_linear >= 0.90 and bic_linear < (bic_step - 5.0):
        # Continuous monotonic trend without discrete structural break
        regime = "gradual_trend"
        detected = False
    elif is_sig and is_meaningful_shift:
        regime = "sustained_level_shift"
        detected = True
    elif best_var_ratio >= variance_ratio_threshold and not is_sig:
        regime = "variance_regime_shift"
        detected = True
    elif r2_linear >= 0.85 and abs(slope) > 1e-3:
        regime = "gradual_trend"
        detected = False
    else:
        regime = "normal"
        detected = False

    return ChangePointResult(
        metric=metric_name,
        change_point_detected=detected,
        change_point_date=change_date if detected else None,
        regime_type=regime,
        pre_change_mean=round(best_mu1, 4),
        post_change_mean=round(best_mu2, 4),
        mean_shift_pct=round(shift_pct, 2),
        pre_change_variance=round(best_var1, 4),
        post_change_variance=round(best_var2, 4),
        variance_ratio=round(best_var_ratio, 2),
        statistical_score=round(abs(best_t_stat), 4),
        test_statistic=round(best_t_stat, 4),
        p_value=round(best_p_val, 6),
        is_statistically_significant=is_sig,
        method=method,
        minimum_segment_size=minimum_segment_size,
        observations_used=n_obs,
        pre_change_period=pre_period,
        post_change_period=post_period,
        details={
            "degrees_of_freedom": round(best_df, 2),
            "delta_sse": round(best_score, 2),
            "bic_step": round(bic_step, 2),
            "bic_linear": round(bic_linear, 2),
            "r2_linear_trend": round(r2_linear, 4),
            "robust_max_z": round(max_rz, 2),
            "candidate_split_index": best_tau,
        },
    )


def run_change_point_detection(
    conn: psycopg.Connection,
    metric: str,
    start_date: date,
    end_date: date,
    product_category: str | None = None,
    minimum_segment_size: int = 5,
    significance_level: float = 0.05,
    variance_ratio_threshold: float = 2.5,
    method: str = "welch_binary_segmentation",
) -> ChangePointSeriesResponse:
    """Fetch time series from database and execute change-point detection."""
    observations = fetch_daily_kpi_series(
        conn=conn,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
        product_category=product_category,
    )

    cp_result = detect_change_point(
        observations=observations,
        minimum_segment_size=minimum_segment_size,
        significance_level=significance_level,
        variance_ratio_threshold=variance_ratio_threshold,
        method=method,
    )

    return ChangePointSeriesResponse(
        metric=metric,
        product_category=product_category,
        start_date=start_date,
        end_date=end_date,
        change_point=cp_result,
        time_series=observations,
    )
