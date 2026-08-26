"""KPI Query Service for RootCause AI.

Extracts all 20 business metrics deterministically from analytical feature marts.
"""

from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row

from apps.analytics.models import KPISummary
from apps.analytics.queries import KPI_SUMMARY_SQL


def get_kpis(conn: psycopg.Connection, start_date: date, end_date: date) -> KPISummary:
    """Retrieve full consolidated KPISummary for a date window."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            KPI_SUMMARY_SQL,
            (
                start_date.isoformat(),
                end_date.isoformat(),
                start_date.isoformat(),
                end_date.isoformat(),
            ),
        )
        row = cur.fetchone()

    if not row:
        return KPISummary(
            start_date=start_date,
            end_date=end_date,
            gmv=0.0,
            delivered_gmv=0.0,
            average_order_value=None,
            revenue_per_customer=None,
            orders_count=0,
            delivered_orders_count=0,
            canceled_orders_count=0,
            items_sold_count=0,
            unique_customers_count=0,
            new_customers_count=0,
            repeat_customers_count=0,
            repeat_buyer_rate_pct=None,
            late_delivery_rate_pct=None,
            avg_delivery_days=None,
            avg_seller_dispatch_days=None,
            avg_carrier_transit_days=None,
            avg_review_score=None,
            negative_review_rate_pct=None,
            freight_revenue=0.0,
            freight_to_gmv_ratio=None,
        )

    def _round_opt(val: Any, decimals: int = 2) -> float | None:
        return round(float(val), decimals) if val is not None else None

    return KPISummary(
        start_date=start_date,
        end_date=end_date,
        gmv=round(float(row["gmv"]), 2),
        delivered_gmv=round(float(row["delivered_gmv"]), 2),
        average_order_value=_round_opt(row["average_order_value"], 2),
        revenue_per_customer=_round_opt(row["revenue_per_customer"], 2),
        orders_count=int(row["orders_count"]),
        delivered_orders_count=int(row["delivered_orders_count"]),
        canceled_orders_count=int(row["canceled_orders_count"]),
        items_sold_count=int(row["items_sold_count"]),
        unique_customers_count=int(row["unique_customers_count"]),
        new_customers_count=int(row["new_customers_count"]),
        repeat_customers_count=int(row["repeat_customers_count"]),
        repeat_buyer_rate_pct=_round_opt(row["repeat_buyer_rate_pct"], 2),
        late_delivery_rate_pct=_round_opt(row["late_delivery_rate_pct"], 2),
        avg_delivery_days=_round_opt(row["avg_delivery_days"], 2),
        avg_seller_dispatch_days=_round_opt(row["avg_seller_dispatch_days"], 2),
        avg_carrier_transit_days=_round_opt(row["avg_carrier_transit_days"], 2),
        avg_review_score=_round_opt(row["avg_review_score"], 2),
        negative_review_rate_pct=_round_opt(row["negative_review_rate_pct"], 2),
        freight_revenue=round(float(row["freight_revenue"]), 2),
        freight_to_gmv_ratio=_round_opt(row["freight_to_gmv_ratio"], 4),
    )


def get_revenue_kpi(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> dict[str, Any]:
    """Extract revenue-focused metrics."""
    kpi = get_kpis(conn, start_date, end_date)
    return {
        "gmv": kpi.gmv,
        "delivered_gmv": kpi.delivered_gmv,
        "average_order_value": kpi.average_order_value,
        "revenue_per_customer": kpi.revenue_per_customer,
    }


def get_order_volume_kpi(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> dict[str, Any]:
    """Extract order volume metrics."""
    kpi = get_kpis(conn, start_date, end_date)
    return {
        "orders_count": kpi.orders_count,
        "delivered_orders_count": kpi.delivered_orders_count,
        "canceled_orders_count": kpi.canceled_orders_count,
        "items_sold_count": kpi.items_sold_count,
    }


def get_customer_kpi(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> dict[str, Any]:
    """Extract customer acquisition and retention metrics."""
    kpi = get_kpis(conn, start_date, end_date)
    return {
        "unique_customers_count": kpi.unique_customers_count,
        "new_customers_count": kpi.new_customers_count,
        "repeat_customers_count": kpi.repeat_customers_count,
        "repeat_buyer_rate_pct": kpi.repeat_buyer_rate_pct,
    }


def get_delivery_kpi(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> dict[str, Any]:
    """Extract operational and fulfillment SLA metrics."""
    kpi = get_kpis(conn, start_date, end_date)
    return {
        "late_delivery_rate_pct": kpi.late_delivery_rate_pct,
        "avg_delivery_days": kpi.avg_delivery_days,
        "avg_seller_dispatch_days": kpi.avg_seller_dispatch_days,
        "avg_carrier_transit_days": kpi.avg_carrier_transit_days,
    }


def get_review_kpi(
    conn: psycopg.Connection, start_date: date, end_date: date
) -> dict[str, Any]:
    """Extract customer satisfaction metrics."""
    kpi = get_kpis(conn, start_date, end_date)
    return {
        "avg_review_score": kpi.avg_review_score,
        "negative_review_rate_pct": kpi.negative_review_rate_pct,
    }
