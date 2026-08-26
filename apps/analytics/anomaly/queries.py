"""SQL Queries for Daily KPI Time-Series Extraction."""

from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row

from apps.analytics.anomaly.models import DailyKPIObservation

# Controlled mapping of approved metrics to parameterized SQL aggregations
# This prevents arbitrary SQL identifiers from being passed into queries.
METRIC_EXPRESSIONS: dict[str, str] = {
    "total_gmv": "COALESCE(SUM(total_gmv), 0.00)::FLOAT",
    "orders_count": "COALESCE(SUM(orders_count), 0)::FLOAT",
    "average_order_value": (
        "CASE WHEN SUM(orders_count) > 0 "
        "THEN (SUM(total_gmv) / SUM(orders_count))::FLOAT "
        "ELSE NULL END"
    ),
    "late_delivery_rate_pct": (
        "CASE WHEN SUM(orders_count) > 0 "
        "THEN (100.0 * SUM(late_delivered_orders_count) / SUM(orders_count))::FLOAT "
        "ELSE NULL END"
    ),
    "delivery": (
        "CASE WHEN SUM(orders_count) > 0 "
        "THEN (100.0 * SUM(late_delivered_orders_count) / SUM(orders_count))::FLOAT "
        "ELSE NULL END"
    ),
    "avg_review_score": "AVG(avg_review_score)::FLOAT",
}


def fetch_daily_kpi_series(
    conn: psycopg.Connection,
    metric: str,
    start_date: date,
    end_date: date,
    product_category: str | None = None,
) -> list[DailyKPIObservation]:
    """Retrieve daily time-series observations for a KPI from fact_daily_kpis."""
    norm_metric = metric.strip().lower()
    if norm_metric not in METRIC_EXPRESSIONS:
        valid_metrics = list(METRIC_EXPRESSIONS.keys())
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported metrics: {valid_metrics}"
        )

    val_expr = METRIC_EXPRESSIONS[norm_metric]

    if product_category:
        query = f"""
        SELECT
            kpi_date AS obs_date,
            {val_expr} AS obs_value
        FROM fact_daily_kpis
        WHERE kpi_date >= %s::DATE 
          AND kpi_date <= %s::DATE
          AND product_category_name = %s
        GROUP BY kpi_date
        ORDER BY kpi_date ASC;
        """
        params: tuple[Any, ...] = (
            start_date.isoformat(),
            end_date.isoformat(),
            product_category,
        )
    else:
        query = f"""
        SELECT
            kpi_date AS obs_date,
            {val_expr} AS obs_value
        FROM fact_daily_kpis
        WHERE kpi_date >= %s::DATE 
          AND kpi_date <= %s::DATE
        GROUP BY kpi_date
        ORDER BY kpi_date ASC;
        """
        params = (start_date.isoformat(), end_date.isoformat())

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    observations: list[DailyKPIObservation] = []
    for r in rows:
        val = round(float(r["obs_value"]), 4) if r["obs_value"] is not None else None
        observations.append(
            DailyKPIObservation(
                date=r["obs_date"],
                metric=norm_metric,
                value=val,
            )
        )

    return observations
