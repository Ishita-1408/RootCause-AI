"""Deterministic Revenue Analysis & Decomposition Engine.

Calculates period-over-period revenue deltas, mathematical volume/AOV decompositions,
and dimensional contribution ranking across customer geography, product categories,
sellers, and order fulfillment statuses.
"""

from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row

from apps.analytics.models import (
    ChangeMetrics,
    DimensionFinding,
    PeriodSummary,
)
from scripts.eda_helpers import format_currency_brl


def fetch_period_summary(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> PeriodSummary:
    """Calculate aggregate revenue, order volume, and AOV for a time interval."""
    query = """
    SELECT
        COALESCE(SUM(merchandise_revenue), 0.00)::FLOAT AS total_revenue,
        COUNT(order_id)::INTEGER AS order_count,
        CASE
            WHEN COUNT(order_id) > 0 
            THEN (
                COALESCE(SUM(merchandise_revenue), 0.00) / COUNT(order_id)
            )::FLOAT
            ELSE 0.0
        END AS average_order_value
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ;
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, (start_date.isoformat(), end_date.isoformat()))
        row = cur.fetchone()

    total_rev = float(row["total_revenue"]) if row else 0.0
    orders_cnt = int(row["order_count"]) if row else 0
    aov = float(row["average_order_value"]) if row else 0.0

    return PeriodSummary(
        start_date=start_date,
        end_date=end_date,
        total_revenue=round(total_rev, 2),
        order_count=orders_cnt,
        average_order_value=round(aov, 2),
    )


def compute_change_metrics(
    current: PeriodSummary, baseline: PeriodSummary
) -> ChangeMetrics:
    """Compute period-over-period delta metrics and exact volume/AOV decomposition."""
    rev_change = current.total_revenue - baseline.total_revenue
    rev_change_pct = (
        (rev_change / baseline.total_revenue) * 100.0
        if baseline.total_revenue > 0
        else (100.0 if current.total_revenue > 0 else 0.0)
    )

    orders_change = current.order_count - baseline.order_count
    orders_change_pct = (
        (orders_change / baseline.order_count) * 100.0
        if baseline.order_count > 0
        else (100.0 if current.order_count > 0 else 0.0)
    )

    aov_change = current.average_order_value - baseline.average_order_value
    aov_change_pct = (
        (aov_change / baseline.average_order_value) * 100.0
        if baseline.average_order_value > 0
        else (100.0 if current.average_order_value > 0 else 0.0)
    )

    # Exact additive decomposition: Volume Effect + AOV Effect = Total Change
    vol_effect = (
        current.order_count - baseline.order_count
    ) * baseline.average_order_value
    aov_eff = current.order_count * (
        current.average_order_value - baseline.average_order_value
    )

    return ChangeMetrics(
        revenue_change=round(rev_change, 2),
        revenue_change_pct=round(rev_change_pct, 2),
        order_count_change=orders_change,
        order_count_change_pct=round(orders_change_pct, 2),
        aov_change=round(aov_change, 2),
        aov_change_pct=round(aov_change_pct, 2),
        volume_effect=round(vol_effect, 2),
        aov_effect=round(aov_eff, 2),
    )


def build_finding_explanation(
    dimension_value: str,
    dimension_name: str,
    current_val: float,
    baseline_val: float,
    abs_change: float,
    contrib_pct: float,
    total_change: float,
) -> str:
    """Generate a deterministic, evidence-backed narrative explanation."""
    dir_word = "growth" if total_change > 0 else "decline"
    item_word = "increased" if abs_change > 0 else "decreased"

    cur_str = format_currency_brl(current_val)
    base_str = format_currency_brl(baseline_val)
    abs_str = format_currency_brl(abs_change)

    if total_change == 0:
        return (
            f"{dimension_value} ({dimension_name}) had {cur_str} "
            f"vs {base_str} in baseline."
        )

    if (total_change > 0 and abs_change > 0) or (total_change < 0 and abs_change < 0):
        return (
            f"{dimension_value} contributed approximately {abs(contrib_pct):.1f}% "
            f"to the total revenue {dir_word} "
            f"({base_str} -> {cur_str}, change: {abs_str})."
        )
    return (
        f"{dimension_value} {item_word} by "
        f"{format_currency_brl(abs(abs_change))} "
        f"({base_str} -> {cur_str}), partially counteracting the "
        f"overall revenue {dir_word}."
    )


def analyze_dimension_breakdown(
    conn: psycopg.Connection,
    dimension: str,
    start_date: date,
    end_date: date,
    baseline_start: date,
    baseline_end: date,
    total_revenue_change: float,
    limit: int = 5,
) -> list[DimensionFinding]:
    """Perform deterministic dimensional slice attribution and contribution ranking."""
    if dimension == "customer_state":
        query = """
        WITH current_period AS (
            SELECT
                COALESCE(customer_state, 'Unknown') AS slice_value,
                SUM(merchandise_revenue) AS revenue
            FROM fact_order_analytics
            WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
            GROUP BY COALESCE(customer_state, 'Unknown')
        ),
        baseline_period AS (
            SELECT
                COALESCE(customer_state, 'Unknown') AS slice_value,
                SUM(merchandise_revenue) AS revenue
            FROM fact_order_analytics
            WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
            GROUP BY COALESCE(customer_state, 'Unknown')
        )
        SELECT
            COALESCE(c.slice_value, b.slice_value) AS slice_value,
            COALESCE(c.revenue, 0.00)::FLOAT AS current_value,
            COALESCE(b.revenue, 0.00)::FLOAT AS baseline_value
        FROM current_period c
        FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
        """
    elif dimension == "order_status":
        query = """
        WITH current_period AS (
            SELECT
                order_status AS slice_value,
                SUM(merchandise_revenue) AS revenue
            FROM fact_order_analytics
            WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
            GROUP BY order_status
        ),
        baseline_period AS (
            SELECT
                order_status AS slice_value,
                SUM(merchandise_revenue) AS revenue
            FROM fact_order_analytics
            WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
            GROUP BY order_status
        )
        SELECT
            COALESCE(c.slice_value, b.slice_value) AS slice_value,
            COALESCE(c.revenue, 0.00)::FLOAT AS current_value,
            COALESCE(b.revenue, 0.00)::FLOAT AS baseline_value
        FROM current_period c
        FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
        """
    elif dimension == "product_category":
        query = """
        WITH current_period AS (
            SELECT
                COALESCE(
                    pc.product_category_name_english,
                    p.product_category_name,
                    'uncategorized'
                ) AS slice_value,
                SUM(oi.price) AS revenue
            FROM fact_order_analytics foa
            JOIN order_items oi ON foa.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_categories pc 
                ON p.product_category_name = pc.product_category_name
            WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND foa.order_purchase_timestamp < (
                  %s::DATE + INTERVAL '1 day'
              )::TIMESTAMPTZ
            GROUP BY COALESCE(
                pc.product_category_name_english,
                p.product_category_name,
                'uncategorized'
            )
        ),
        baseline_period AS (
            SELECT
                COALESCE(
                    pc.product_category_name_english,
                    p.product_category_name,
                    'uncategorized'
                ) AS slice_value,
                SUM(oi.price) AS revenue
            FROM fact_order_analytics foa
            JOIN order_items oi ON foa.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_categories pc 
                ON p.product_category_name = pc.product_category_name
            WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND foa.order_purchase_timestamp < (
                  %s::DATE + INTERVAL '1 day'
              )::TIMESTAMPTZ
            GROUP BY COALESCE(
                pc.product_category_name_english,
                p.product_category_name,
                'uncategorized'
            )
        )
        SELECT
            COALESCE(c.slice_value, b.slice_value) AS slice_value,
            COALESCE(c.revenue, 0.00)::FLOAT AS current_value,
            COALESCE(b.revenue, 0.00)::FLOAT AS baseline_value
        FROM current_period c
        FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
        """
    elif dimension == "seller":
        query = """
        WITH current_period AS (
            SELECT
                oi.seller_id AS slice_value,
                SUM(oi.price) AS revenue
            FROM fact_order_analytics foa
            JOIN order_items oi ON foa.order_id = oi.order_id
            WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND foa.order_purchase_timestamp < (
                  %s::DATE + INTERVAL '1 day'
              )::TIMESTAMPTZ
            GROUP BY oi.seller_id
        ),
        baseline_period AS (
            SELECT
                oi.seller_id AS slice_value,
                SUM(oi.price) AS revenue
            FROM fact_order_analytics foa
            JOIN order_items oi ON foa.order_id = oi.order_id
            WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
              AND foa.order_purchase_timestamp < (
                  %s::DATE + INTERVAL '1 day'
              )::TIMESTAMPTZ
            GROUP BY oi.seller_id
        )
        SELECT
            COALESCE(c.slice_value, b.slice_value) AS slice_value,
            COALESCE(c.revenue, 0.00)::FLOAT AS current_value,
            COALESCE(b.revenue, 0.00)::FLOAT AS baseline_value
        FROM current_period c
        FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
        """
    else:
        raise ValueError(f"Unsupported dimension: {dimension}")

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            query,
            (
                start_date.isoformat(),
                end_date.isoformat(),
                baseline_start.isoformat(),
                baseline_end.isoformat(),
            ),
        )
        rows = cur.fetchall()

    raw_findings: list[dict[str, Any]] = []
    for r in rows:
        c_val = float(r["current_value"])
        b_val = float(r["baseline_value"])
        abs_diff = c_val - b_val
        pct_diff = (
            (abs_diff / b_val) * 100.0 if b_val > 0 else (100.0 if c_val > 0 else 0.0)
        )
        contrib_pct = (
            (abs_diff / total_revenue_change) * 100.0
            if total_revenue_change != 0
            else 0.0
        )

        raw_findings.append(
            {
                "slice_value": str(r["slice_value"]),
                "current_val": round(c_val, 2),
                "baseline_val": round(b_val, 2),
                "abs_diff": round(abs_diff, 2),
                "pct_diff": round(pct_diff, 2),
                "contrib_pct": round(contrib_pct, 2),
            }
        )

    # Rank findings by contribution aligned with the direction of total change
    if total_revenue_change < 0:
        raw_findings.sort(key=lambda x: x["abs_diff"])
    else:
        raw_findings.sort(key=lambda x: x["abs_diff"], reverse=True)

    findings: list[DimensionFinding] = []
    for rank_idx, item in enumerate(raw_findings[:limit], start=1):
        expl = build_finding_explanation(
            dimension_value=item["slice_value"],
            dimension_name=dimension,
            current_val=item["current_val"],
            baseline_val=item["baseline_val"],
            abs_change=item["abs_diff"],
            contrib_pct=item["contrib_pct"],
            total_change=total_revenue_change,
        )

        findings.append(
            DimensionFinding(
                dimension=dimension,  # type: ignore[arg-type]
                dimension_value=item["slice_value"],
                metric="revenue",
                current_value=item["current_val"],
                baseline_value=item["baseline_val"],
                absolute_change=item["abs_diff"],
                percentage_change=item["pct_diff"],
                contribution_percentage=item["contrib_pct"],
                rank=rank_idx,
                explanation=expl,
            )
        )

    return findings
