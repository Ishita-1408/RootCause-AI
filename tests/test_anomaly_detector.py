"""Unit tests for Phase 5A Daily Time-Series Anomaly Detector."""

from collections.abc import Sequence
from datetime import date, timedelta

import numpy as np

from apps.analytics.anomaly.detector import detect_anomalies
from apps.analytics.anomaly.models import DailyKPIObservation


def _make_series(
    values: Sequence[float | None], start: date = date(2018, 1, 1)
) -> list[DailyKPIObservation]:
    """Helper to generate a list of DailyKPIObservation objects."""
    return [
        DailyKPIObservation(
            date=start + timedelta(days=i),
            metric="total_gmv",
            value=v,
        )
        for i, v in enumerate(values)
    ]


# 1. Normal stable series -> No anomaly
def test_normal_stable_series() -> None:
    """Test that stable, low-variance series generates zero anomalies."""
    # 10 days of values near 100 with small variance
    values = [100.0, 102.0, 99.0, 101.0, 100.0, 103.0, 98.0, 101.0, 100.0, 99.0]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    assert len(results) == 10
    anomalies = [r for r in results if r.is_anomaly]
    assert len(anomalies) == 0


# 2. Sudden large increase -> Positive anomaly
def test_sudden_large_increase() -> None:
    """Test detection of an acute positive spike on Day 8."""
    values = [100.0, 102.0, 99.0, 101.0, 100.0, 103.0, 98.0, 160.0]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    day8_result = results[7]
    assert day8_result.is_anomaly is True
    assert day8_result.direction == "increase"
    assert day8_result.z_score is not None
    assert day8_result.z_score > 2.0
    assert day8_result.severity in ["warning", "critical"]


# 3. Sudden large decrease -> Negative anomaly
def test_sudden_large_decrease() -> None:
    """Test detection of an acute negative drop on Day 8."""
    values = [100.0, 102.0, 99.0, 101.0, 100.0, 103.0, 98.0, 40.0]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    day8_result = results[7]
    assert day8_result.is_anomaly is True
    assert day8_result.direction == "decrease"
    assert day8_result.z_score is not None
    assert day8_result.z_score < -2.0


# 4. Constant series -> No divide-by-zero error
def test_constant_series_zero_std() -> None:
    """Test that zero variance series safely returns no anomaly without error."""
    values = [100.0] * 10
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    assert len(results) == 10
    for r in results:
        assert r.is_anomaly is False
        assert r.z_score is None
        assert r.severity == "normal"


# 5. Insufficient history -> No anomaly
def test_insufficient_history() -> None:
    """Test that observations before minimum_history is reached are not flagged."""
    values = [100.0, 102.0, 99.0, 101.0, 200.0]  # Spike on day 5 (history < 7)
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    assert len(results) == 5
    for r in results:
        assert r.is_anomaly is False
        assert r.z_score is None


# 6. Missing values -> Safe handling
def test_missing_values_handling() -> None:
    """Test that None values in time-series are safely handled without crash."""
    values = [100.0, 102.0, None, 101.0, 100.0, 103.0, 98.0, 101.0, None, 100.0]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=5
    )

    assert len(results) == 10
    assert results[2].observed_value is None
    assert results[2].is_anomaly is False
    assert results[8].observed_value is None
    assert results[8].is_anomaly is False


# 7. First observation -> No anomaly
def test_first_observation() -> None:
    """Test that the very first observation is never flagged."""
    values = [100.0]
    observations = _make_series(values)
    results = detect_anomalies(observations)

    assert len(results) == 1
    assert results[0].is_anomaly is False
    assert results[0].baseline_mean is None
    assert results[0].z_score is None


# 8. Boundary: z = 2.0 -> Warning severity
def test_boundary_warning_severity() -> None:
    """Test that z-score between 2.0 and 3.0 produces warning severity."""
    # Baseline with mean = 100, std = 10
    # Day 8 observed = 120 -> z = (120 - 100) / 10 = +2.0
    history = [100.0 + 10.0 * x for x in [-1.5, -0.5, 0.0, 0.5, 1.5, -1.0, 1.0]]
    mean_hist = float(np.mean(history))
    std_hist = float(np.std(history, ddof=1))
    target_val = mean_hist + 2.05 * std_hist  # z ~ 2.05

    values = history + [target_val]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    day8 = results[7]
    assert day8.is_anomaly is True
    assert day8.severity == "warning"
    assert day8.direction == "increase"


# 9. Boundary: z = 3.0 -> Critical severity
def test_boundary_critical_severity() -> None:
    """Test that z-score >= 3.0 produces critical severity."""
    history = [100.0, 102.0, 99.0, 101.0, 100.0, 103.0, 98.0]
    mean_hist = float(np.mean(history))
    std_hist = float(np.std(history, ddof=1))
    target_val = mean_hist + 3.5 * std_hist  # z = 3.5

    values = history + [target_val]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    day8 = results[7]
    assert day8.is_anomaly is True
    assert day8.severity == "critical"
    assert day8.z_score is not None
    assert day8.z_score >= 3.0


# 10. Data Leakage Verification: Baseline strictly excludes today's value
def test_no_lookahead_data_leakage() -> None:
    """Verify that today's value is strictly excluded from its own baseline calculation.

    If today's value (1000.0) were leaked into the baseline:
    baseline mean would be inflated from ~100 to ~228, and baseline std would explode.
    """
    history = [100.0, 102.0, 99.0, 101.0, 100.0, 103.0, 98.0]
    expected_baseline_mean = round(float(np.mean(history)), 4)
    expected_baseline_std = round(float(np.std(history, ddof=1)), 4)

    # Massive outlier on Day 8
    values = history + [1000.0]
    observations = _make_series(values)
    results = detect_anomalies(
        observations, window=7, z_threshold=2.0, minimum_history=7
    )

    day8 = results[7]

    # Baseline for Day 8 must match the pure prior 7 days
    assert day8.baseline_mean == expected_baseline_mean
    assert day8.baseline_std == expected_baseline_std

    # Leakage check: if 1000 were included, mean would be ~212.85
    assert day8.baseline_mean < 150.0
    assert day8.is_anomaly is True
    assert day8.severity == "critical"
