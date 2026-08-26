"""SQL Query Layer for Root-Cause Drill-Down Engine.

Executes controlled, parameterized SQL queries against fact_order_analytics
and related marts to extract observed and baseline daily figures.
"""

from datetime import date
from typing import TypedDict

import psycopg
from psycopg.rows import dict_row


class MetricSummaryRecord(TypedDict):
    """Headline metric and operational indicators for a period."""

    orders_count: float
    total_gmv: float
    average_order_value: float
    late_delivery_rate: float
    avg_delivery_days: float
    cancellation_rate: float
    avg_review_score: float


class SliceRecord(TypedDict):
    """Observed vs. daily baseline values for a specific slice."""

    slice_value: str
    observed_value: float
    baseline_value: float


def fetch_date_metrics(
    conn: psycopg.Connection, target_date: date
) -> MetricSummaryRecord:
    """Fetch single-day metric aggregates from fact_order_analytics."""
    query = """
    SELECT
        COUNT(DISTINCT foa.order_id)::FLOAT AS orders_count,
        COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT AS total_gmv,
        CASE
            WHEN COUNT(DISTINCT foa.order_id) > 0
            THEN (COALESCE(SUM(foa.merchandise_revenue), 0.00)
                  / COUNT(DISTINCT foa.order_id))::FLOAT
            ELSE 0.0
        END AS average_order_value,
        CASE
            WHEN COUNT(CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.is_late_delivery = TRUE THEN 1 END)
                  / COUNT(CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END))::FLOAT
            ELSE 0.0
        END AS late_delivery_rate,
        COALESCE(AVG(foa.total_delivery_days), 0.00)::FLOAT AS avg_delivery_days,
        CASE
            WHEN COUNT(DISTINCT foa.order_id) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.order_status = 'canceled' THEN 1 END)
                  / COUNT(DISTINCT foa.order_id))::FLOAT
            ELSE 0.0
        END AS cancellation_rate,
        COALESCE(AVG(foa.review_score), 0.00)::FLOAT AS avg_review_score
    FROM fact_order_analytics foa
    WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ;
    """
    params = (target_date.isoformat(), target_date.isoformat())

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        row = cur.fetchone()

    if not row:
        return {
            "orders_count": 0.0,
            "total_gmv": 0.0,
            "average_order_value": 0.0,
            "late_delivery_rate": 0.0,
            "avg_delivery_days": 0.0,
            "cancellation_rate": 0.0,
            "avg_review_score": 0.0,
        }

    return {
        "orders_count": round(float(row["orders_count"]), 2),
        "total_gmv": round(float(row["total_gmv"]), 2),
        "average_order_value": round(float(row["average_order_value"]), 2),
        "late_delivery_rate": round(float(row["late_delivery_rate"]), 2),
        "avg_delivery_days": round(float(row["avg_delivery_days"]), 2),
        "cancellation_rate": round(float(row["cancellation_rate"]), 2),
        "avg_review_score": round(float(row["avg_review_score"]), 2),
    }


def fetch_baseline_daily_metrics(
    conn: psycopg.Connection,
    baseline_start: date,
    baseline_end: date,
    days: int,
) -> MetricSummaryRecord:
    """Fetch baseline daily average metric aggregates over the baseline window."""
    query = """
    SELECT
        (COUNT(DISTINCT foa.order_id)::FLOAT / %s) AS orders_count,
        (COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT / %s) AS total_gmv,
        CASE
            WHEN COUNT(DISTINCT foa.order_id) > 0
            THEN (COALESCE(SUM(foa.merchandise_revenue), 0.00)
                  / COUNT(DISTINCT foa.order_id))::FLOAT
            ELSE 0.0
        END AS average_order_value,
        CASE
            WHEN COUNT(CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.is_late_delivery = TRUE THEN 1 END)
                  / COUNT(CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END))::FLOAT
            ELSE 0.0
        END AS late_delivery_rate,
        COALESCE(AVG(foa.total_delivery_days), 0.00)::FLOAT AS avg_delivery_days,
        CASE
            WHEN COUNT(DISTINCT foa.order_id) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.order_status = 'canceled' THEN 1 END)
                  / COUNT(DISTINCT foa.order_id))::FLOAT
            ELSE 0.0
        END AS cancellation_rate,
        COALESCE(AVG(foa.review_score), 0.00)::FLOAT AS avg_review_score
    FROM fact_order_analytics foa
    WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ;
    """
    safe_days = max(1, days)
    params = (
        safe_days,
        safe_days,
        baseline_start.isoformat(),
        baseline_end.isoformat(),
    )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        row = cur.fetchone()

    if not row:
        return {
            "orders_count": 0.0,
            "total_gmv": 0.0,
            "average_order_value": 0.0,
            "late_delivery_rate": 0.0,
            "avg_delivery_days": 0.0,
            "cancellation_rate": 0.0,
            "avg_review_score": 0.0,
        }

    return {
        "orders_count": round(float(row["orders_count"]), 2),
        "total_gmv": round(float(row["total_gmv"]), 2),
        "average_order_value": round(float(row["average_order_value"]), 2),
        "late_delivery_rate": round(float(row["late_delivery_rate"]), 2),
        "avg_delivery_days": round(float(row["avg_delivery_days"]), 2),
        "cancellation_rate": round(float(row["cancellation_rate"]), 2),
        "avg_review_score": round(float(row["avg_review_score"]), 2),
    }


def fetch_dimension_slices(
    conn: psycopg.Connection,
    dimension: str,
    anomaly_date: date,
    baseline_start: date,
    baseline_end: date,
    days: int,
) -> list[SliceRecord]:
    """Fetch observed vs daily baseline GMV per slice using FULL OUTER JOIN."""
    safe_days = max(1, days)

    if dimension == "product_category":
        dim_col = "COALESCE(p.product_category_name, 'uncategorized')"
        from_clause = (
            "fact_order_analytics foa "
            "JOIN order_items oi ON foa.order_id = oi.order_id "
            "JOIN products p ON oi.product_id = p.product_id"
        )
        agg_val = "COALESCE(SUM(oi.price), 0.00)::FLOAT"
    elif dimension == "customer_state":
        dim_col = "COALESCE(foa.customer_state, 'Unknown')"
        from_clause = "fact_order_analytics foa"
        agg_val = "COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT"
    elif dimension == "seller":
        dim_col = "oi.seller_id"
        from_clause = (
            "fact_order_analytics foa JOIN order_items oi ON foa.order_id = oi.order_id"
        )
        agg_val = "COALESCE(SUM(oi.price), 0.00)::FLOAT"
    else:
        return []

    query = f"""
    WITH obs AS (
        SELECT
            {dim_col} AS slice_val,
            {agg_val} AS obs_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_col}
    ),
    base AS (
        SELECT
            {dim_col} AS slice_val,
            ({agg_val} / %s)::FLOAT AS base_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_col}
    )
    SELECT
        COALESCE(o.slice_val, b.slice_val) AS slice_value,
        COALESCE(o.obs_val, 0.00)::FLOAT AS observed_value,
        COALESCE(b.base_val, 0.00)::FLOAT AS baseline_value
    FROM obs o
    FULL OUTER JOIN base b ON o.slice_val = b.slice_val;
    """
    params = (
        anomaly_date.isoformat(),
        anomaly_date.isoformat(),
        safe_days,
        baseline_start.isoformat(),
        baseline_end.isoformat(),
    )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {
            "slice_value": str(r["slice_value"]),
            "observed_value": round(float(r["observed_value"]), 2),
            "baseline_value": round(float(r["baseline_value"]), 2),
        }
        for r in rows
    ]
