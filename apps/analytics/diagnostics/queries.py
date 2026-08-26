"""SQL Query Layer for Root-Cause Diagnostic Engine.

Executes parameterized analytical queries across fact_order_analytics to compute
period metrics, operational fulfillment lead times, review distributions,
and normalized dimensional slices.
"""

from datetime import date
from typing import Any, TypedDict

import psycopg
from psycopg.rows import dict_row


class PeriodAggregateRecord(TypedDict):
    """Aggregate metrics for a specific time period."""

    orders_count: float
    total_gmv: float
    average_order_value: float
    late_delivery_rate_pct: float
    avg_review_score: float
    seller_dispatch_days: float
    carrier_transit_days: float
    cancellation_rate_pct: float
    negative_review_rate_pct: float
    one_star_review_rate_pct: float
    two_star_review_rate_pct: float


class DiagnosticSliceRecord(TypedDict):
    """Dimensional slice record for comparison."""

    slice_value: str
    actual_value: float
    baseline_value: float


def fetch_period_diagnostics(
    conn: psycopg.Connection,
    start_date: date,
    end_date: date,
    category: str | None = None,
    customer_state: str | None = None,
) -> PeriodAggregateRecord:
    """Fetch complete diagnostic aggregates for a time window."""
    where_clauses = [
        "foa.order_purchase_timestamp >= %s::TIMESTAMPTZ",
        "foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ",
    ]
    params: list[Any] = [start_date.isoformat(), end_date.isoformat()]

    join_clause = ""
    if category:
        join_clause = (
            "JOIN order_items oi ON foa.order_id = oi.order_id "
            "JOIN products p ON oi.product_id = p.product_id"
        )
        where_clauses.append("p.product_category_name = %s")
        params.append(category)

    if customer_state:
        where_clauses.append("foa.customer_state = %s")
        params.append(customer_state)

    where_sql = " AND ".join(where_clauses)

    query = f"""
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
        END AS late_delivery_rate_pct,
        COALESCE(AVG(foa.review_score), 0.00)::FLOAT AS avg_review_score,
        COALESCE(AVG(foa.seller_dispatch_days), 0.00)::FLOAT AS seller_dispatch_days,
        COALESCE(AVG(foa.carrier_transit_days), 0.00)::FLOAT AS carrier_transit_days,
        CASE
            WHEN COUNT(DISTINCT foa.order_id) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.order_status = 'canceled' THEN 1 END)
                  / COUNT(DISTINCT foa.order_id))::FLOAT
            ELSE 0.0
        END AS cancellation_rate_pct,
        CASE
            WHEN COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.review_score <= 2 THEN 1 END)
                  / COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END))::FLOAT
            ELSE 0.0
        END AS negative_review_rate_pct,
        CASE
            WHEN COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.review_score = 1 THEN 1 END)
                  / COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END))::FLOAT
            ELSE 0.0
        END AS one_star_review_rate_pct,
        CASE
            WHEN COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END) > 0
            THEN (100.0 * COUNT(CASE WHEN foa.review_score = 2 THEN 1 END)
                  / COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END))::FLOAT
            ELSE 0.0
        END AS two_star_review_rate_pct
    FROM fact_order_analytics foa
    {join_clause}
    WHERE {where_sql};
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, tuple(params))
        row = cur.fetchone()

    if not row:
        return {
            "orders_count": 0.0,
            "total_gmv": 0.0,
            "average_order_value": 0.0,
            "late_delivery_rate_pct": 0.0,
            "avg_review_score": 0.0,
            "seller_dispatch_days": 0.0,
            "carrier_transit_days": 0.0,
            "cancellation_rate_pct": 0.0,
            "negative_review_rate_pct": 0.0,
            "one_star_review_rate_pct": 0.0,
            "two_star_review_rate_pct": 0.0,
        }

    return {
        "orders_count": round(float(row["orders_count"]), 2),
        "total_gmv": round(float(row["total_gmv"]), 2),
        "average_order_value": round(float(row["average_order_value"]), 2),
        "late_delivery_rate_pct": round(float(row["late_delivery_rate_pct"]), 2),
        "avg_review_score": round(float(row["avg_review_score"]), 2),
        "seller_dispatch_days": round(float(row["seller_dispatch_days"]), 2),
        "carrier_transit_days": round(float(row["carrier_transit_days"]), 2),
        "cancellation_rate_pct": round(float(row["cancellation_rate_pct"]), 2),
        "negative_review_rate_pct": round(float(row["negative_review_rate_pct"]), 2),
        "one_star_review_rate_pct": round(float(row["one_star_review_rate_pct"]), 2),
        "two_star_review_rate_pct": round(float(row["two_star_review_rate_pct"]), 2),
    }


def fetch_dimension_slices_for_diagnostic(
    conn: psycopg.Connection,
    dimension: str,
    metric: str,
    actual_start: date,
    actual_end: date,
    baseline_start: date,
    baseline_end: date,
    norm_factor: float = 1.0,
) -> list[DiagnosticSliceRecord]:
    """Fetch dimension slices comparing actual period vs normalized baseline period."""
    if dimension == "product_category_name":
        dim_col = "COALESCE(p.product_category_name, 'uncategorized')"
        from_clause = (
            "fact_order_analytics foa "
            "JOIN order_items oi ON foa.order_id = oi.order_id "
            "JOIN products p ON oi.product_id = p.product_id"
        )
        agg_expr = (
            "COALESCE(SUM(oi.price), 0.00)::FLOAT"
            if metric == "total_gmv"
            else "COUNT(DISTINCT foa.order_id)::FLOAT"
        )
    elif dimension == "seller_id":
        dim_col = "oi.seller_id"
        from_clause = (
            "fact_order_analytics foa JOIN order_items oi ON foa.order_id = oi.order_id"
        )
        agg_expr = (
            "COALESCE(SUM(oi.price), 0.00)::FLOAT"
            if metric == "total_gmv"
            else "COUNT(DISTINCT foa.order_id)::FLOAT"
        )
    elif dimension == "customer_state":
        dim_col = "COALESCE(foa.customer_state, 'Unknown')"
        from_clause = "fact_order_analytics foa"
        agg_expr = (
            "COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT"
            if metric == "total_gmv"
            else "COUNT(DISTINCT foa.order_id)::FLOAT"
        )
    elif dimension == "payment_type":
        dim_col = "COALESCE(foa.primary_payment_type, 'unknown')"
        from_clause = "fact_order_analytics foa"
        agg_expr = (
            "COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT"
            if metric == "total_gmv"
            else "COUNT(DISTINCT foa.order_id)::FLOAT"
        )
    else:
        raise ValueError(f"Unsupported diagnostic dimension: {dimension}")

    query = f"""
    WITH actual_data AS (
        SELECT
            {dim_col} AS slice_val,
            {agg_expr} AS metric_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_col}
    ),
    baseline_data AS (
        SELECT
            {dim_col} AS slice_val,
            {agg_expr} AS metric_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_col}
    )
    SELECT
        COALESCE(a.slice_val, b.slice_val) AS slice_value,
        COALESCE(a.metric_val, 0.00)::FLOAT AS actual_value,
        (COALESCE(b.metric_val, 0.00) * %s)::FLOAT AS baseline_value
    FROM actual_data a
    FULL OUTER JOIN baseline_data b ON a.slice_val = b.slice_val;
    """

    params = (
        actual_start.isoformat(),
        actual_end.isoformat(),
        baseline_start.isoformat(),
        baseline_end.isoformat(),
        norm_factor,
    )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {
            "slice_value": str(r["slice_value"]),
            "actual_value": round(float(r["actual_value"]), 2),
            "baseline_value": round(float(r["baseline_value"]), 2),
        }
        for r in rows
    ]
