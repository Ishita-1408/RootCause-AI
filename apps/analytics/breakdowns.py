"""Dimensional Breakdown & Contribution Engine for RootCause AI.

Slices business metrics across dimensions (geography, category, merchant,
status, tender) and calculates unclamped mathematical contribution percentages.
"""

from datetime import date
from typing import TypedDict

import psycopg
from psycopg.rows import dict_row

from apps.analytics.models import (
    DimensionalSlice,
    DimensionBreakdownResponse,
)
from apps.analytics.queries import (
    BREAKDOWN_CUSTOMER_STATE_SQL,
    BREAKDOWN_ORDER_STATUS_SQL,
    BREAKDOWN_PAYMENT_TYPE_SQL,
    BREAKDOWN_PRODUCT_CATEGORY_SQL,
    BREAKDOWN_SELLER_SQL,
)

SUPPORTED_DIMENSIONS = {
    "customer_state": BREAKDOWN_CUSTOMER_STATE_SQL,
    "product_category": BREAKDOWN_PRODUCT_CATEGORY_SQL,
    "seller": BREAKDOWN_SELLER_SQL,
    "order_status": BREAKDOWN_ORDER_STATUS_SQL,
    "payment_type": BREAKDOWN_PAYMENT_TYPE_SQL,
}

SUPPORTED_METRICS = ["gmv", "revenue", "orders", "orders_count", "freight"]


class _RawSlice(TypedDict):
    slice_value: str
    current_value: float
    baseline_value: float
    absolute_change: float


class _EnrichedSlice(_RawSlice):
    percentage_change: float | None
    contribution_percentage: float | None


def get_dimensional_breakdown(
    conn: psycopg.Connection,
    metric: str,
    dimension: str,
    current_start: date,
    current_end: date,
    baseline_start: date,
    baseline_end: date,
    limit: int = 20,
) -> DimensionBreakdownResponse:
    """Execute dimensional contribution attribution across selected dimension."""
    norm_dim = dimension.strip().lower()
    norm_metric = metric.strip().lower()

    if norm_dim not in SUPPORTED_DIMENSIONS:
        dims_list = list(SUPPORTED_DIMENSIONS.keys())
        raise ValueError(f"Unsupported dimension '{dimension}'. Supported: {dims_list}")

    if norm_metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported: {SUPPORTED_METRICS}"
        )

    sql_query = SUPPORTED_DIMENSIONS[norm_dim]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql_query,
            (
                current_start.isoformat(),
                current_end.isoformat(),
                baseline_start.isoformat(),
                baseline_end.isoformat(),
            ),
        )
        rows = cur.fetchall()

    col_prefix = "revenue"
    if norm_metric in ["orders", "orders_count"]:
        col_prefix = "orders"
    elif norm_metric == "freight":
        col_prefix = "freight"

    raw_slices: list[_RawSlice] = []
    tot_cur: float = 0.0
    tot_base: float = 0.0

    for r in rows:
        c_val = float(r[f"current_{col_prefix}"])
        b_val = float(r[f"baseline_{col_prefix}"])
        tot_cur += c_val
        tot_base += b_val
        raw_slices.append(
            {
                "slice_value": str(r["slice_value"]),
                "current_value": round(c_val, 2),
                "baseline_value": round(b_val, 2),
                "absolute_change": round(c_val - b_val, 2),
            }
        )

    total_change = round(tot_cur - tot_base, 2)

    enriched_slices: list[_EnrichedSlice] = []
    for s in raw_slices:
        b_val = s["baseline_value"]
        c_val = s["current_value"]
        diff = s["absolute_change"]

        pct_change: float | None = None
        if b_val > 0:
            pct_change = round((diff / b_val) * 100.0, 2)
        elif b_val == 0 and c_val > 0:
            pct_change = 100.0
        elif b_val == 0 and c_val == 0:
            pct_change = 0.0

        contrib_pct: float | None = None
        if total_change != 0:
            contrib_pct = round((diff / total_change) * 100.0, 2)

        enriched_slices.append(
            {
                "slice_value": s["slice_value"],
                "current_value": s["current_value"],
                "baseline_value": s["baseline_value"],
                "absolute_change": s["absolute_change"],
                "percentage_change": pct_change,
                "contribution_percentage": contrib_pct,
            }
        )

    # Sort: if total dropped, largest drops rank 1; if total grew, largest gains rank 1
    if total_change < 0:
        enriched_slices.sort(key=lambda x: x["absolute_change"])
    else:
        enriched_slices.sort(key=lambda x: x["absolute_change"], reverse=True)

    final_slices: list[DimensionalSlice] = []
    for rank_idx, item in enumerate(enriched_slices[:limit], start=1):
        final_slices.append(
            DimensionalSlice(
                slice_value=item["slice_value"],
                current_value=item["current_value"],
                baseline_value=item["baseline_value"],
                absolute_change=item["absolute_change"],
                percentage_change=item["percentage_change"],
                contribution_percentage=item["contribution_percentage"],
                rank=rank_idx,
            )
        )

    return DimensionBreakdownResponse(
        metric=norm_metric,
        dimension=norm_dim,
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        total_current_value=round(tot_cur, 2),
        total_baseline_value=round(tot_base, 2),
        total_change=total_change,
        slices=final_slices,
    )
