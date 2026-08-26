"""Period Comparison Engine for RootCause AI.

Computes exact period-over-period deltas, percentage changes, and directionality
across all business metrics without relying on heuristic estimates.
"""

from datetime import date
from typing import Any

import psycopg

from apps.analytics.metrics import get_kpis
from apps.analytics.models import MetricComparison, PeriodComparisonResponse


def compare_single_metric(
    metric_name: str,
    current_val: float | int | None,
    baseline_val: float | int | None,
) -> MetricComparison:
    """Compute deterministic absolute change, percentage change, and direction."""
    if current_val is None or baseline_val is None:
        abs_change = (
            round(float(current_val) - float(baseline_val), 2)
            if (current_val is not None and baseline_val is not None)
            else None
        )
        return MetricComparison(
            metric=metric_name,
            current_value=current_val,
            baseline_value=baseline_val,
            absolute_change=abs_change,
            percentage_change=None,
            direction="undefined",
        )

    cur_f = float(current_val)
    base_f = float(baseline_val)
    abs_change_f = round(cur_f - base_f, 2)

    # Percentage change calculation with zero baseline protection
    pct_change: float | None = None
    if base_f > 0:
        pct_change = round((abs_change_f / base_f) * 100.0, 2)
    elif base_f == 0 and cur_f > 0:
        pct_change = 100.0
    elif base_f == 0 and cur_f == 0:
        pct_change = 0.0

    direction: Any = "unchanged"
    if abs_change_f > 0:
        direction = "increase"
    elif abs_change_f < 0:
        direction = "decrease"

    # Match integer types if inputs were integer
    ret_cur: float | int = (
        int(current_val) if isinstance(current_val, int) else round(cur_f, 2)
    )
    ret_base: float | int = (
        int(baseline_val) if isinstance(baseline_val, int) else round(base_f, 2)
    )
    ret_abs: float | int = (
        int(abs_change_f)
        if isinstance(current_val, int) and isinstance(baseline_val, int)
        else abs_change_f
    )

    return MetricComparison(
        metric=metric_name,
        current_value=ret_cur,
        baseline_value=ret_base,
        absolute_change=ret_abs,
        percentage_change=pct_change,
        direction=direction,
    )


def compare_periods(
    conn: psycopg.Connection,
    current_start: date,
    current_end: date,
    baseline_start: date,
    baseline_end: date,
) -> PeriodComparisonResponse:
    """Compare all consolidated KPIs between current and baseline windows."""
    cur_kpis = get_kpis(conn, current_start, current_end)
    base_kpis = get_kpis(conn, baseline_start, baseline_end)

    metric_fields = [
        "gmv",
        "delivered_gmv",
        "average_order_value",
        "revenue_per_customer",
        "orders_count",
        "delivered_orders_count",
        "canceled_orders_count",
        "items_sold_count",
        "unique_customers_count",
        "new_customers_count",
        "repeat_customers_count",
        "repeat_buyer_rate_pct",
        "late_delivery_rate_pct",
        "avg_delivery_days",
        "avg_seller_dispatch_days",
        "avg_carrier_transit_days",
        "avg_review_score",
        "negative_review_rate_pct",
        "freight_revenue",
        "freight_to_gmv_ratio",
    ]

    comparisons: dict[str, MetricComparison] = {}
    for field in metric_fields:
        c_val = getattr(cur_kpis, field)
        b_val = getattr(base_kpis, field)
        comparisons[field] = compare_single_metric(field, c_val, b_val)

    return PeriodComparisonResponse(
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        comparisons=comparisons,
    )
