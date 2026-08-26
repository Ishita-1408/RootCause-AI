"""Statistical Rolling Time-Series Anomaly Detector for RootCause AI.

Uses a shifted (lagged) rolling window to calculate rolling mean (mu) and standard
deviation (sigma) without look-ahead data leakage, computing standardized z-scores.
"""

from datetime import date
from typing import Literal

import pandas as pd
import psycopg

from apps.analytics.anomaly.models import (
    AnomalyDetectionResponse,
    AnomalyResult,
    DailyKPIObservation,
)
from apps.analytics.anomaly.queries import fetch_daily_kpi_series


def detect_anomalies(
    observations: list[DailyKPIObservation],
    window: int = 7,
    z_threshold: float = 2.0,
    minimum_history: int = 7,
) -> list[AnomalyResult]:
    """Detect statistical anomalies across a sequence of daily KPI observations.

    Data Leakage Rule:
    The baseline (rolling mean and standard deviation) for observation at time t
    is calculated strictly over prior observations [t - window, ..., t - 1] by
    applying `.shift(1)` before the rolling calculation. Today's value is never
    included in its own baseline.
    """
    if not observations:
        return []

    metric_name = observations[0].metric

    df = pd.DataFrame(
        [{"date": obs.date, "value": obs.value} for obs in observations]
    ).sort_values("date")

    # Shift by 1 to strictly exclude current day's value from baseline
    shifted_val = df["value"].shift(1)

    rolling_mean_series = shifted_val.rolling(
        window=window, min_periods=minimum_history
    ).mean()
    rolling_std_series = shifted_val.rolling(
        window=window, min_periods=minimum_history
    ).std(ddof=1)

    results: list[AnomalyResult] = []

    for idx in range(len(df)):
        obs_date: date = df.iloc[idx]["date"]
        obs_val = df.iloc[idx]["value"]
        b_mean = rolling_mean_series.iloc[idx]
        b_std = rolling_std_series.iloc[idx]

        # Case 1: Missing observed value
        if pd.isna(obs_val):
            results.append(
                AnomalyResult(
                    date=obs_date,
                    metric=metric_name,
                    observed_value=None,
                    baseline_mean=(
                        round(float(b_mean), 4) if pd.notna(b_mean) else None
                    ),
                    baseline_std=(round(float(b_std), 4) if pd.notna(b_std) else None),
                    z_score=None,
                    severity="normal",
                    is_anomaly=False,
                    direction="normal",
                )
            )
            continue

        val_f = float(obs_val)

        # Case 2: Insufficient historical baseline or zero variance
        if pd.isna(b_mean) or pd.isna(b_std) or float(b_std) <= 1e-9:
            results.append(
                AnomalyResult(
                    date=obs_date,
                    metric=metric_name,
                    observed_value=round(val_f, 4),
                    baseline_mean=(
                        round(float(b_mean), 4) if pd.notna(b_mean) else None
                    ),
                    baseline_std=(round(float(b_std), 4) if pd.notna(b_std) else None),
                    z_score=None,
                    severity="normal",
                    is_anomaly=False,
                    direction="normal",
                )
            )
            continue

        mean_f = float(b_mean)
        std_f = float(b_std)

        # Compute z-score: z = (observed - mu) / sigma
        z_val = (val_f - mean_f) / std_f
        abs_z = abs(z_val)
        is_anom = abs_z >= z_threshold

        # Severity ranking
        severity: Literal["normal", "warning", "critical"] = "normal"
        if abs_z >= 3.0:
            severity = "critical"
        elif abs_z >= 2.0:
            severity = "warning"

        # Directionality
        direction: Literal["increase", "decrease", "normal"] = "normal"
        if is_anom:
            direction = "increase" if z_val > 0 else "decrease"

        results.append(
            AnomalyResult(
                date=obs_date,
                metric=metric_name,
                observed_value=round(val_f, 4),
                baseline_mean=round(mean_f, 4),
                baseline_std=round(std_f, 4),
                z_score=round(z_val, 4),
                severity=severity,
                is_anomaly=is_anom,
                direction=direction,
            )
        )

    return results


def run_anomaly_detection(
    conn: psycopg.Connection,
    metric: str,
    start_date: date,
    end_date: date,
    product_category: str | None = None,
    window: int = 7,
    z_threshold: float = 2.0,
    minimum_history: int = 7,
) -> AnomalyDetectionResponse:
    """Extract daily KPI series from database and run anomaly detection."""
    observations = fetch_daily_kpi_series(
        conn=conn,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
        product_category=product_category,
    )

    results = detect_anomalies(
        observations=observations,
        window=window,
        z_threshold=z_threshold,
        minimum_history=minimum_history,
    )

    anomalies_count = sum(1 for r in results if r.is_anomaly)

    from apps.analytics.change_detection.detector import detect_change_point

    change_point = (
        detect_change_point(observations) if len(observations) >= 10 else None
    )

    return AnomalyDetectionResponse(
        metric=metric,
        product_category=product_category,
        start_date=start_date,
        end_date=end_date,
        window=window,
        z_threshold=z_threshold,
        minimum_history=minimum_history,
        total_observations=len(results),
        anomalies_count=anomalies_count,
        results=results,
        change_point=change_point,
    )
