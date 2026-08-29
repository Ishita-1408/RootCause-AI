"""Statistical Confidence Interval and Significance Engine (Phase K)."""

import math
from collections.abc import Callable, Sequence

import numpy as np

from apps.analytics.change_detection.detector import student_t_pvalue
from apps.analytics.statistics.models import (
    ConfidenceInterval,
    StatisticalSignificance,
)


def _approx_student_t_crit(df: float, alpha: float = 0.05) -> float:
    """Approximate Student's t critical value for two-tailed (1 - alpha) level."""
    if df <= 0:
        return 1.96
    p = 1.0 - alpha / 2.0
    # Rational approximation for standard normal quantile
    if p >= 0.5:
        t_val = math.sqrt(-2.0 * math.log(1.0 - p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = t_val - (c0 + c1 * t_val + c2 * (t_val**2)) / (
            1.0 + d1 * t_val + d2 * (t_val**2) + d3 * (t_val**3)
        )
    else:
        t_val = math.sqrt(-2.0 * math.log(p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = -(
            t_val
            - (c0 + c1 * t_val + c2 * (t_val**2))
            / (1.0 + d1 * t_val + d2 * (t_val**2) + d3 * (t_val**3))
        )

    # Cornish-Fisher expansion for Student's t
    term1 = z
    term2 = (z**3 + z) / (4.0 * df)
    term3 = (5.0 * (z**5) + 16.0 * (z**3) + 3.0 * z) / (96.0 * (df**2))
    return term1 + term2 + term3


def compute_mean_confidence_interval(
    sample: Sequence[float],
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Compute confidence interval for a single sample mean."""
    clean = [float(x) for x in sample if x is not None and not math.isnan(x)]
    n = len(clean)

    if n < 2:
        val = clean[0] if n == 1 else 0.0
        return ConfidenceInterval(
            point_estimate=round(val, 4),
            lower_bound=None,
            upper_bound=None,
            confidence_level=confidence_level,
            standard_error=None,
            method="insufficient_data",
            is_computable=False,
        )

    arr = np.array(clean, dtype=float)
    mean_val = float(np.mean(arr))
    var_val = float(np.var(arr, ddof=1))
    std_val = math.sqrt(var_val) if var_val > 0 else 0.0
    se = std_val / math.sqrt(n)

    if se < 1e-12:
        return ConfidenceInterval(
            point_estimate=round(mean_val, 4),
            lower_bound=round(mean_val, 4),
            upper_bound=round(mean_val, 4),
            confidence_level=confidence_level,
            standard_error=0.0,
            method="welch_t",
            is_computable=True,
        )

    df = float(n - 1)
    alpha = 1.0 - confidence_level
    t_crit = _approx_student_t_crit(df, alpha)
    margin = t_crit * se

    return ConfidenceInterval(
        point_estimate=round(mean_val, 4),
        lower_bound=round(mean_val - margin, 4),
        upper_bound=round(mean_val + margin, 4),
        confidence_level=confidence_level,
        standard_error=round(se, 4),
        method="welch_t",
        is_computable=True,
    )


def compute_welch_confidence_interval(
    sample1: Sequence[float],
    sample2: Sequence[float],
    confidence_level: float = 0.95,
    alpha: float = 0.05,
) -> tuple[ConfidenceInterval, StatisticalSignificance]:
    """Compute two-sample Welch's t confidence interval and hypothesis test."""
    c1 = [float(x) for x in sample1 if x is not None and not math.isnan(x)]
    c2 = [float(x) for x in sample2 if x is not None and not math.isnan(x)]

    n1, n2 = len(c1), len(c2)
    if n1 < 2 or n2 < 2:
        diff = (float(c2[0]) if n2 > 0 else 0.0) - (float(c1[0]) if n1 > 0 else 0.0)
        ci = ConfidenceInterval(
            point_estimate=round(diff, 4),
            lower_bound=None,
            upper_bound=None,
            confidence_level=confidence_level,
            standard_error=None,
            method="insufficient_data",
            is_computable=False,
        )
        sig = StatisticalSignificance(
            test_name="Welch's Two-Sample t-test",
            test_statistic=None,
            p_value=None,
            degrees_of_freedom=None,
            alpha=alpha,
            is_statistically_significant=False,
        )
        return ci, sig

    arr1 = np.array(c1, dtype=float)
    arr2 = np.array(c2, dtype=float)

    mu1, mu2 = float(np.mean(arr1)), float(np.mean(arr2))
    var1 = float(np.var(arr1, ddof=1))
    var2 = float(np.var(arr2, ddof=1))

    diff = mu2 - mu1
    se_diff = math.sqrt((var1 / n1) + (var2 / n2))

    if se_diff < 1e-12:
        ci = ConfidenceInterval(
            point_estimate=round(diff, 4),
            lower_bound=round(diff, 4),
            upper_bound=round(diff, 4),
            confidence_level=confidence_level,
            standard_error=0.0,
            method="welch_t",
            is_computable=True,
        )
        sig = StatisticalSignificance(
            test_name="Welch's Two-Sample t-test",
            test_statistic=0.0,
            p_value=1.0,
            degrees_of_freedom=float(n1 + n2 - 2),
            alpha=alpha,
            is_statistically_significant=False,
        )
        return ci, sig

    t_stat = diff / se_diff
    # Welch-Satterthwaite degrees of freedom
    num_df = ((var1 / n1) + (var2 / n2)) ** 2
    den_df = (((var1 / n1) ** 2) / max(n1 - 1, 1)) + (
        ((var2 / n2) ** 2) / max(n2 - 1, 1)
    )
    df_val = num_df / den_df if den_df > 0 else float(n1 + n2 - 2)

    p_val = student_t_pvalue(abs(t_stat), df_val)
    t_crit = _approx_student_t_crit(df_val, 1.0 - confidence_level)
    margin = t_crit * se_diff

    ci = ConfidenceInterval(
        point_estimate=round(diff, 4),
        lower_bound=round(diff - margin, 4),
        upper_bound=round(diff + margin, 4),
        confidence_level=confidence_level,
        standard_error=round(se_diff, 4),
        method="welch_t",
        is_computable=True,
    )

    sig = StatisticalSignificance(
        test_name="Welch's Two-Sample t-test",
        test_statistic=round(t_stat, 4),
        p_value=round(p_val, 6),
        degrees_of_freedom=round(df_val, 2),
        alpha=alpha,
        is_statistically_significant=(p_val <= alpha),
    )

    return ci, sig


def compute_proportion_confidence_interval(
    count: float,
    total: float,
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Compute Wilson score interval for a binomial proportion/share."""
    if total <= 0 or count < 0:
        return ConfidenceInterval(
            point_estimate=0.0,
            lower_bound=None,
            upper_bound=None,
            confidence_level=confidence_level,
            standard_error=None,
            method="insufficient_data",
            is_computable=False,
        )

    p_hat = min(max(count / total, 0.0), 1.0)
    alpha = 1.0 - confidence_level
    z = _approx_student_t_crit(df=1000.0, alpha=alpha)

    denom = 1.0 + (z**2) / total
    center = (p_hat + (z**2) / (2.0 * total)) / denom
    var_term = max(0.0, (p_hat * (1.0 - p_hat) / total) + (z**2) / (4.0 * (total**2)))
    margin = (z * math.sqrt(var_term)) / denom
    se_var = max(0.0, p_hat * (1.0 - p_hat) / total)
    se = math.sqrt(se_var) if total > 1 else 0.0

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return ConfidenceInterval(
        point_estimate=round(p_hat, 4),
        lower_bound=round(lower, 4),
        upper_bound=round(upper, 4),
        confidence_level=confidence_level,
        standard_error=round(se, 4),
        method="wilson_score",
        is_computable=True,
    )


def compute_bootstrap_confidence_interval(
    sample: Sequence[float],
    statistic_fn: Callable[[np.ndarray], float],
    n_resamples: int = 500,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> ConfidenceInterval:
    """Compute non-parametric percentile bootstrap confidence interval."""
    clean = [float(x) for x in sample if x is not None and not math.isnan(x)]
    n = len(clean)

    if n < 4:
        val = statistic_fn(np.array(clean, dtype=float)) if n > 0 else 0.0
        return ConfidenceInterval(
            point_estimate=round(val, 4),
            lower_bound=None,
            upper_bound=None,
            confidence_level=confidence_level,
            standard_error=None,
            method="insufficient_data",
            is_computable=False,
        )

    arr = np.array(clean, dtype=float)
    point_est = float(statistic_fn(arr))

    rng = np.random.default_rng(random_seed)
    boot_stats = np.empty(n_resamples, dtype=float)

    for i in range(n_resamples):
        resample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = statistic_fn(resample)

    alpha = 1.0 - confidence_level
    low_pct = (alpha / 2.0) * 100.0
    high_pct = (1.0 - alpha / 2.0) * 100.0

    lower_bound = float(np.percentile(boot_stats, low_pct))
    upper_bound = float(np.percentile(boot_stats, high_pct))
    se_boot = float(np.std(boot_stats, ddof=1))

    return ConfidenceInterval(
        point_estimate=round(point_est, 4),
        lower_bound=round(lower_bound, 4),
        upper_bound=round(upper_bound, 4),
        confidence_level=confidence_level,
        standard_error=round(se_boot, 4),
        method="bootstrap",
        is_computable=True,
    )
