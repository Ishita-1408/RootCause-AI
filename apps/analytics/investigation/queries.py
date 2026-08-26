"""SQL Query Layer for Root-Cause Dimensional Contribution Analysis.

Executes controlled, parameterized SQL queries that calculate Current and Baseline
aggregations for each approved dimension and metric pair, combining them via
FULL OUTER JOIN.
"""

from datetime import date
from typing import Any, TypedDict

import psycopg
from psycopg.rows import dict_row

SUPPORTED_METRICS = [
    "total_gmv",
    "orders_count",
    "average_order_value",
    "late_delivery_rate_pct",
    "avg_review_score",
]

SUPPORTED_DIMENSIONS = [
    "customer_state",
    "product_category_name",
    "seller_id",
    "order_status",
    "payment_type",
]


class DimensionSliceRecord(TypedDict):
    """Raw record from a dimensional comparison query."""

    slice_value: str
    current_value: float
    baseline_value: float


def _get_dimension_column(dimension: str) -> str:
    """Return SQL expression for the dimension slice."""
    if dimension == "customer_state":
        return "COALESCE(foa.customer_state, 'Unknown')"
    if dimension == "order_status":
        return "foa.order_status"
    if dimension == "payment_type":
        return "COALESCE(foa.primary_payment_type, 'unknown')"
    if dimension == "seller_id":
        return "oi.seller_id"
    if dimension == "product_category_name":
        return "COALESCE(p.product_category_name, 'uncategorized')"
    raise ValueError(f"Unsupported dimension: {dimension}")


def _get_metric_agg_expression(metric: str) -> str:
    """Return aggregation expression for the target metric."""
    if metric == "total_gmv":
        return "COALESCE(SUM(foa.merchandise_revenue), 0.00)::FLOAT"
    if metric == "orders_count":
        return "COUNT(DISTINCT foa.order_id)::FLOAT"
    if metric == "average_order_value":
        return (
            "CASE WHEN COUNT(DISTINCT foa.order_id) > 0 "
            "THEN (COALESCE(SUM(foa.merchandise_revenue), 0.00) "
            "/ COUNT(DISTINCT foa.order_id))::FLOAT "
            "ELSE 0.0 END"
        )
    if metric == "late_delivery_rate_pct":
        return (
            "CASE WHEN COUNT("
            "CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END"
            ") > 0 THEN (100.0 * COUNT("
            "CASE WHEN foa.is_late_delivery = TRUE THEN 1 END"
            ") / COUNT("
            "CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END"
            "))::FLOAT ELSE 0.0 END"
        )
    if metric == "avg_review_score":
        return "COALESCE(AVG(foa.review_score), 0.00)::FLOAT"
    raise ValueError(f"Unsupported metric: {metric}")


def _get_item_level_metric_agg(metric: str) -> str:
    """Return aggregation expression for item-level joined queries."""
    if metric == "total_gmv":
        return "COALESCE(SUM(oi.price), 0.00)::FLOAT"
    if metric == "orders_count":
        return "COUNT(DISTINCT foa.order_id)::FLOAT"
    if metric == "average_order_value":
        return (
            "CASE WHEN COUNT(DISTINCT foa.order_id) > 0 "
            "THEN (COALESCE(SUM(oi.price), 0.00) "
            "/ COUNT(DISTINCT foa.order_id))::FLOAT "
            "ELSE 0.0 END"
        )
    if metric == "late_delivery_rate_pct":
        return (
            "CASE WHEN COUNT("
            "CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END"
            ") > 0 THEN (100.0 * COUNT("
            "CASE WHEN foa.is_late_delivery = TRUE THEN 1 END"
            ") / COUNT("
            "CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END"
            "))::FLOAT ELSE 0.0 END"
        )
    if metric == "avg_review_score":
        return "COALESCE(AVG(foa.review_score), 0.00)::FLOAT"
    raise ValueError(f"Unsupported metric: {metric}")


def build_contribution_query(metric: str, dimension: str) -> str:
    """Build controlled SQL query for comparing dimension slices."""
    is_item_joined = dimension in ["seller_id", "product_category_name"]
    dim_expr = _get_dimension_column(dimension)
    agg_expr = (
        _get_item_level_metric_agg(metric)
        if is_item_joined
        else _get_metric_agg_expression(metric)
    )

    from_clause = "fact_order_analytics foa"
    if dimension == "seller_id":
        from_clause = (
            "fact_order_analytics foa JOIN order_items oi ON foa.order_id = oi.order_id"
        )
    elif dimension == "product_category_name":
        from_clause = (
            "fact_order_analytics foa "
            "JOIN order_items oi ON foa.order_id = oi.order_id "
            "JOIN products p ON oi.product_id = p.product_id"
        )

    return f"""
    WITH current_period AS (
        SELECT
            {dim_expr} AS slice_value,
            {agg_expr} AS metric_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_expr}
    ),
    baseline_period AS (
        SELECT
            {dim_expr} AS slice_value,
            {agg_expr} AS metric_val
        FROM {from_clause}
        WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
          AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
        GROUP BY {dim_expr}
    )
    SELECT
        COALESCE(c.slice_value, b.slice_value) AS slice_value,
        COALESCE(c.metric_val, 0.00)::FLOAT AS current_value,
        COALESCE(b.metric_val, 0.00)::FLOAT AS baseline_value
    FROM current_period c
    FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
    """


def fetch_metric_by_dimension(
    conn: psycopg.Connection,
    metric: str,
    dimension: str,
    current_start: date,
    current_end: date,
    baseline_start: date,
    baseline_end: date,
) -> list[DimensionSliceRecord]:
    """Fetch current vs baseline values for all dimension slices."""
    norm_metric = metric.strip().lower()
    norm_dim = dimension.strip().lower()

    if norm_metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported: {SUPPORTED_METRICS}"
        )
    if norm_dim not in SUPPORTED_DIMENSIONS:
        raise ValueError(
            f"Unsupported dimension '{dimension}'. Supported: {SUPPORTED_DIMENSIONS}"
        )

    query = build_contribution_query(norm_metric, norm_dim)
    params: tuple[Any, ...] = (
        current_start.isoformat(),
        current_end.isoformat(),
        baseline_start.isoformat(),
        baseline_end.isoformat(),
    )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {
            "slice_value": str(r["slice_value"]),
            "current_value": round(float(r["current_value"]), 4),
            "baseline_value": round(float(r["baseline_value"]), 4),
        }
        for r in rows
    ]
