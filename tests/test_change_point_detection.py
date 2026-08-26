"""Comprehensive Statistical Unit Tests for Change-Point Detection (Phase J)."""

from datetime import date, timedelta

from apps.analytics.anomaly.models import DailyKPIObservation
from apps.analytics.change_detection.detector import (
    detect_change_point,
    student_t_pvalue,
)


def test_student_t_pvalue_tail_probabilities() -> None:
    """Verify Student's t distribution p-value implementation."""
    assert student_t_pvalue(0.0, 10.0) == 1.0
    # t = 2.228 at df = 10 gives two-tailed p ~ 0.05
    p_05 = student_t_pvalue(2.228, 10.0)
    assert 0.045 <= p_05 <= 0.055

    # High t gives p close to 0
    p_high = student_t_pvalue(10.0, 20.0)
    assert p_high < 1e-5


def test_isolated_spike_detection() -> None:
    """Verify isolated spike is flagged as isolated_anomaly without change point."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=250.0 if i == 10 else 100.0 + (i % 2) * 2.0,
        )
        for i in range(20)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is False
    assert res.regime_type == "isolated_anomaly"
    assert res.change_point_date is None


def test_sustained_level_shift_detection() -> None:
    """Verify detection of sustained structural mean shift."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=100.0 if i < 10 else 180.0,
        )
        for i in range(20)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is True
    assert res.regime_type == "sustained_level_shift"
    assert res.change_point_date == base_date + timedelta(days=10)
    assert res.mean_shift_pct is not None
    assert round(res.mean_shift_pct, 1) == 80.0
    assert res.is_statistically_significant is True


def test_variance_regime_shift_detection() -> None:
    """Verify detection of variance expansion without mean shift."""
    base_date = date(2017, 3, 1)
    obs = []
    for i in range(24):
        val = 100.0 + (2.0 if i < 12 else 25.0) * (1.0 if i % 2 == 0 else -1.0)
        obs.append(
            DailyKPIObservation(
                date=base_date + timedelta(days=i), metric="total_gmv", value=val
            )
        )
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is True
    assert res.regime_type == "variance_regime_shift"
    assert res.variance_ratio is not None
    assert res.variance_ratio >= 2.5


def test_gradual_linear_trend_non_detection() -> None:
    """Verify gradual monotonic trend is not classified as a structural break."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=100.0 + 4.0 * float(i),
        )
        for i in range(20)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is False
    assert res.regime_type == "gradual_trend"


def test_constant_series_zero_variance() -> None:
    """Verify constant series handling without division by zero."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i), metric="total_gmv", value=150.0
        )
        for i in range(15)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is False
    assert res.regime_type == "normal"
    assert res.pre_change_variance == 0.0
    assert res.post_change_variance == 0.0


def test_insufficient_data_short_series() -> None:
    """Verify short time series below minimum segment threshold."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i), metric="total_gmv", value=100.0 + i
        )
        for i in range(3)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is False
    assert res.regime_type == "insufficient_data"


def test_missing_dates_and_nan_values() -> None:
    """Verify missing dates and intermittent null values are skipped safely."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=None if i in (2, 5, 12) else (100.0 if i < 10 else 160.0),
        )
        for i in range(20)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is True
    assert res.regime_type == "sustained_level_shift"
    assert res.observations_used == 17


def test_negative_values_series() -> None:
    """Verify support for series containing negative metric values."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="profit_delta",
            value=-50.0 if i < 8 else 20.0,
        )
        for i in range(16)
    ]
    res = detect_change_point(obs, minimum_segment_size=4)
    assert res.change_point_detected is True
    assert res.regime_type == "sustained_level_shift"


def test_deterministic_repeated_execution() -> None:
    """Verify change-point detection produces bitwise identical results on rerun."""
    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=100.0 if i < 10 else 150.0,
        )
        for i in range(20)
    ]
    res1 = detect_change_point(obs, minimum_segment_size=4)
    res2 = detect_change_point(obs, minimum_segment_size=4)
    assert res1.model_dump() == res2.model_dump()


def test_cusum_detector() -> None:
    """Verify CUSUM detector identifies sustained mean shift."""
    from apps.analytics.change_point import detect_cusum_change_point

    base_date = date(2017, 3, 1)
    dates = [base_date + timedelta(days=i) for i in range(20)]
    values = [100.0 if i < 10 else 160.0 for i in range(20)]

    res = detect_cusum_change_point(dates, values, minimum_segment_size=3)
    assert res.detected is True
    assert res.change_point_date == base_date + timedelta(days=10)
    assert res.detection_method == "cusum"
    assert res.persistence == "PERSISTENT_SHIFT"


def test_pelt_detector() -> None:
    """Verify PELT detector with L2 cost and BIC penalty."""
    from apps.analytics.change_point import detect_pelt_change_point

    base_date = date(2017, 3, 1)
    dates = [base_date + timedelta(days=i) for i in range(20)]
    values = [100.0 if i < 10 else 160.0 for i in range(20)]

    res = detect_pelt_change_point(dates, values, minimum_segment_size=3)
    assert res.detected is True
    assert res.change_point_date == base_date + timedelta(days=10)
    assert res.detection_method == "pelt"
    assert res.persistence == "PERSISTENT_SHIFT"


def test_rolling_baseline_detector() -> None:
    """Verify transparent rolling baseline fallback detector."""
    from apps.analytics.change_point import detect_rolling_baseline

    base_date = date(2017, 3, 1)
    dates = [base_date + timedelta(days=i) for i in range(6)]
    values = [100.0, 101.0, 99.0, 150.0, 152.0, 149.0]

    res = detect_rolling_baseline(dates, values, minimum_segment_size=2)
    assert res.detected is True
    assert res.detection_method == "rolling_baseline"


def test_persistence_evaluation_spike_vs_persistent() -> None:
    """Verify persistence classification distinguishes spikes from persistent shifts."""
    from apps.analytics.change_point import evaluate_persistence

    # 1. Single day spike
    spike_vals = [100.0] * 10 + [250.0] + [100.0] * 9
    p_class, p_score, p_days, r_type = evaluate_persistence(
        values=spike_vals,
        change_idx=10,
        pre_mean=100.0,
        post_mean=115.0,
        is_significant=True,
    )
    assert p_class == "SPIKE"
    assert r_type == "isolated_anomaly"

    # 2. Persistent shift
    shift_vals = [100.0] * 10 + [160.0] * 10
    p_class2, p_score2, p_days2, r_type2 = evaluate_persistence(
        values=shift_vals,
        change_idx=10,
        pre_mean=100.0,
        post_mean=160.0,
        is_significant=True,
    )
    assert p_class2 == "PERSISTENT_SHIFT"
    assert r_type2 == "sustained_level_shift"


def test_method_selection_auto() -> None:
    """Verify smart auto method selection by sample size."""
    from apps.analytics.change_point import select_detection_method

    assert select_detection_method(20) == "pelt"
    assert select_detection_method(10) == "cusum"
    assert select_detection_method(5) == "rolling_baseline"
    assert select_detection_method(2) == "insufficient_data"


def test_run_change_point_analysis_orchestration() -> None:
    """Verify unified orchestration function run_change_point_analysis."""
    from apps.analytics.change_point import run_change_point_analysis

    base_date = date(2017, 3, 1)
    obs = [
        DailyKPIObservation(
            date=base_date + timedelta(days=i),
            metric="total_gmv",
            value=100.0 if i < 10 else 160.0,
        )
        for i in range(20)
    ]
    res = run_change_point_analysis(obs, metric="total_gmv", method="auto")
    assert res.detected is True
    assert res.change_point_date == base_date + timedelta(days=10)
