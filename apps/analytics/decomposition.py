"""Descriptive Revenue Decomposition Engine for RootCause AI.

Decomposes period-over-period revenue variations into exact volume vs. price (AOV)
effects using deterministic descriptive arithmetic (Revenue = Orders x AOV).

IMPORTANT ARCHITECTURAL DISTINCTION:
This is a mathematical descriptive decomposition of observed accounting metrics.
It is NOT an econometric or causal inference attribution.
"""

from datetime import date

import psycopg

from apps.analytics.metrics import get_kpis
from apps.analytics.models import RevenueDecomposition


def get_revenue_decomposition(
    conn: psycopg.Connection,
    current_start: date,
    current_end: date,
    baseline_start: date,
    baseline_end: date,
) -> RevenueDecomposition:
    """Compute exact additive volume vs. price decomposition of revenue change.

    Formula:
        ΔRevenue = R1 - R0
        Volume Effect = (Orders1 - Orders0) * AOV0
        Price Effect  = Orders1 * (AOV1 - AOV0)
    Identity:
        Volume Effect + Price Effect = ΔRevenue (Exact additive identity)
    """
    cur_kpi = get_kpis(conn, current_start, current_end)
    base_kpi = get_kpis(conn, baseline_start, baseline_end)

    cur_rev = cur_kpi.gmv
    base_rev = base_kpi.gmv
    tot_rev_change = round(cur_rev - base_rev, 2)

    cur_orders = cur_kpi.orders_count
    base_orders = base_kpi.orders_count
    orders_diff = cur_orders - base_orders
    orders_diff_pct = (
        round((orders_diff / base_orders) * 100.0, 2) if base_orders > 0 else None
    )

    cur_aov = cur_kpi.average_order_value or 0.0
    base_aov = base_kpi.average_order_value or 0.0
    aov_diff = round(cur_aov - base_aov, 2)
    aov_diff_pct = round((aov_diff / base_aov) * 100.0, 2) if base_aov > 0 else None

    # Exact additive decomposition using unrounded AOV for cent-level conservation
    raw_base_aov = (base_rev / base_orders) if base_orders > 0 else 0.0
    vol_effect = round(orders_diff * raw_base_aov, 2)
    price_eff = round(tot_rev_change - vol_effect, 2)

    return RevenueDecomposition(
        decomposition_type="descriptive_decomposition",
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        current_revenue=cur_rev,
        baseline_revenue=base_rev,
        total_revenue_change=tot_rev_change,
        current_orders=cur_orders,
        baseline_orders=base_orders,
        orders_change=orders_diff,
        orders_change_pct=orders_diff_pct,
        current_aov=cur_aov,
        baseline_aov=base_aov,
        aov_change=aov_diff,
        aov_change_pct=aov_diff_pct,
        volume_effect=vol_effect,
        price_effect=price_eff,
    )
