"""Root-Cause Drill-Down Engine for RootCause AI.

Executes deterministic multi-dimensional root-cause investigations:
1. Compares observed anomaly date against preceding baseline window
2. Performs volume vs. AOV revenue decomposition
3. Drills down into Product Category, Customer State, Seller, and Operational dimensions
4. Ranks contributors by absolute contribution share
5. Produces deterministic, non-causal executive synthesis
"""

from datetime import timedelta
from typing import Literal

import psycopg

from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    VolumeValueDecomposition,
)
from apps.analytics.rootcause.queries import (
    fetch_baseline_daily_metrics,
    fetch_date_metrics,
    fetch_dimension_slices,
)
from apps.analytics.rootcause.scoring import (
    calculate_slice_contributors,
    decompose_volume_and_aov,
)
from scripts.eda_helpers import format_currency_brl

STANDARD_LIMITATION = (
    "These findings identify descriptive associations and mathematical "
    "contribution patterns; they do not establish counterfactual causal relationships."
)


def investigate_root_cause(
    conn: psycopg.Connection,
    request: RootCauseInvestigationRequest,
) -> RootCauseInvestigationResponse:
    """Execute complete deterministic root-cause drill-down investigation."""
    anomaly_date = request.anomaly_date
    comp_days = request.comparison_days

    baseline_end = anomaly_date - timedelta(days=1)
    baseline_start = baseline_end - timedelta(days=comp_days - 1)

    # 1. Fetch observed and baseline daily metrics
    obs_m = fetch_date_metrics(conn=conn, target_date=anomaly_date)
    base_m = fetch_baseline_daily_metrics(
        conn=conn,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        days=comp_days,
    )

    # 2. Extract target metric values
    if request.metric == "total_gmv":
        obs_val = obs_m["total_gmv"]
        base_val = base_m["total_gmv"]
    elif request.metric == "orders_count":
        obs_val = obs_m["orders_count"]
        base_val = base_m["orders_count"]
    elif request.metric == "average_order_value":
        obs_val = obs_m["average_order_value"]
        base_val = base_m["average_order_value"]
    elif request.metric == "late_delivery_rate_pct":
        obs_val = obs_m["late_delivery_rate"]
        base_val = base_m["late_delivery_rate"]
    elif request.metric == "avg_review_score":
        obs_val = obs_m["avg_review_score"]
        base_val = base_m["avg_review_score"]
    else:
        raise ValueError(f"Unsupported metric '{request.metric}'")

    abs_change = round(obs_val - base_val, 2)
    pct_change: float | None = None
    if base_val > 0:
        pct_change = round((abs_change / base_val) * 100.0, 2)
    elif base_val == 0 and obs_val > 0:
        pct_change = 100.0
    elif base_val == 0 and obs_val == 0:
        pct_change = 0.0

    direction: Literal["increase", "decrease", "unchanged"] = "unchanged"
    if abs_change > 0:
        direction = "increase"
    elif abs_change < 0:
        direction = "decrease"

    summary = AnomalySummary(
        metric=request.metric,
        anomaly_date=anomaly_date,
        baseline_start_date=baseline_start,
        baseline_end_date=baseline_end,
        observed_value=obs_val,
        baseline_value=base_val,
        absolute_change=abs_change,
        percentage_change=pct_change,
        direction=direction,
    )

    # 3. Volume vs. Value (AOV) Decomposition
    decomposition: VolumeValueDecomposition | None = None
    if request.metric in ["total_gmv", "orders_count", "average_order_value"]:
        decomposition = decompose_volume_and_aov(
            observed_orders=obs_m["orders_count"],
            baseline_orders=base_m["orders_count"],
            observed_aov=obs_m["average_order_value"],
            baseline_aov=base_m["average_order_value"],
        )

    # 4. Dimensional Drill-Downs
    all_ranked_contributors: list[DimensionContributor] = []
    dim_map = {
        "product_category": "product_category",
        "customer_state": "customer_state",
        "seller": "seller",
    }

    total_gmv_change = obs_m["total_gmv"] - base_m["total_gmv"]
    slice_denominator = (
        abs_change if request.metric == "total_gmv" else total_gmv_change
    )

    for req_dim in request.dimensions:
        if req_dim in dim_map:
            slices = fetch_dimension_slices(
                conn=conn,
                dimension=req_dim,
                anomaly_date=anomaly_date,
                baseline_start=baseline_start,
                baseline_end=baseline_end,
                days=comp_days,
            )
            contributors = calculate_slice_contributors(
                slices=slices,
                dimension_name=req_dim,
                total_metric_change=slice_denominator,
                max_results=request.max_results,
            )
            all_ranked_contributors.extend(contributors)

    # Global ranking across all returned slice contributors
    all_ranked_contributors.sort(key=lambda x: abs(x.absolute_change), reverse=True)
    for idx, c in enumerate(all_ranked_contributors, start=1):
        c.rank = idx

    # 5. Operational Indicators
    op_indicators = OperationalIndicators(
        observed_late_delivery_rate=obs_m["late_delivery_rate"],
        baseline_late_delivery_rate=base_m["late_delivery_rate"],
        late_delivery_rate_change=round(
            obs_m["late_delivery_rate"] - base_m["late_delivery_rate"], 2
        ),
        observed_avg_delivery_days=obs_m["avg_delivery_days"],
        baseline_avg_delivery_days=base_m["avg_delivery_days"],
        avg_delivery_days_change=round(
            obs_m["avg_delivery_days"] - base_m["avg_delivery_days"], 2
        ),
        observed_cancellation_rate=obs_m["cancellation_rate"],
        baseline_cancellation_rate=base_m["cancellation_rate"],
        cancellation_rate_change=round(
            obs_m["cancellation_rate"] - base_m["cancellation_rate"], 2
        ),
        observed_avg_review_score=obs_m["avg_review_score"],
        baseline_avg_review_score=base_m["avg_review_score"],
        avg_review_score_change=round(
            obs_m["avg_review_score"] - base_m["avg_review_score"], 2
        ),
    )

    # 6. Formulate Deterministic Explanation
    pct_str = f"{pct_change:+.1f}%" if pct_change is not None else "N/A"
    metric_upper = request.metric.upper()

    explanation_paragraphs: list[str] = []

    # Paragraph 1: Headline Movement
    explanation_paragraphs.append(
        f"{metric_upper} {direction}d {pct_str} on {anomaly_date} compared with "
        f"the previous {comp_days}-day baseline ({baseline_start} to {baseline_end})."
    )

    # Paragraph 2: Volume vs. AOV
    if decomposition:
        vol_pct_chg = "N/A"
        if decomposition.baseline_orders > 0:
            vol_delta = decomposition.observed_orders - decomposition.baseline_orders
            vol_pct_chg = f"{(vol_delta / decomposition.baseline_orders * 100.0):+.1f}%"

        aov_pct_chg = "N/A"
        if decomposition.baseline_aov > 0:
            aov_delta = decomposition.observed_aov - decomposition.baseline_aov
            aov_pct_chg = f"{(aov_delta / decomposition.baseline_aov * 100.0):+.1f}%"

        obs_aov_str = format_currency_brl(decomposition.observed_aov)
        base_aov_str = format_currency_brl(decomposition.baseline_aov)
        explanation_paragraphs.append(
            f"Order volume shifted {vol_pct_chg} "
            f"({decomposition.observed_orders:,.0f} vs "
            f"{decomposition.baseline_orders:,.0f} baseline), while AOV "
            f"shifted {aov_pct_chg} ({obs_aov_str} vs {base_aov_str} baseline)."
        )

    # Paragraph 3: Top Contributors
    top_cat = next(
        (c for c in all_ranked_contributors if c.dimension == "product_category"),
        None,
    )
    top_state = next(
        (c for c in all_ranked_contributors if c.dimension == "customer_state"),
        None,
    )
    contrib_details = []
    if top_cat:
        cat_c_pct = (
            f"{top_cat.contribution_pct:.1f}%"
            if top_cat.contribution_pct is not None
            else "N/A"
        )
        cat_chg_str = format_currency_brl(top_cat.absolute_change)
        contrib_details.append(
            f"category '{top_cat.dimension_value}' ({cat_c_pct} share, {cat_chg_str})"
        )
    if top_state:
        state_c_pct = (
            f"{top_state.contribution_pct:.1f}%"
            if top_state.contribution_pct is not None
            else "N/A"
        )
        state_chg_str = format_currency_brl(top_state.absolute_change)
        contrib_details.append(
            f"state '{top_state.dimension_value}' "
            f"({state_c_pct} share, {state_chg_str})"
        )

    if contrib_details:
        explanation_paragraphs.append(
            "The largest observed contributors to this movement were "
            + " and ".join(contrib_details)
            + "."
        )

    # Paragraph 4: Operational Context
    op_late_obs = op_indicators.observed_late_delivery_rate
    op_late_base = op_indicators.baseline_late_delivery_rate
    op_days_obs = op_indicators.observed_avg_delivery_days
    op_rev_obs = op_indicators.observed_avg_review_score
    op_rev_base = op_indicators.baseline_avg_review_score

    explanation_paragraphs.append(
        f"Operational indicators showed late delivery rate at "
        f"{op_late_obs:.1f}% (vs {op_late_base:.1f}% baseline), "
        f"average delivery duration of {op_days_obs:.1f} days, and "
        f"average review score of {op_rev_obs:.2f} (vs {op_rev_base:.2f})."
    )

    # Paragraph 5: Limitation
    explanation_paragraphs.append(STANDARD_LIMITATION)

    explanation = "\n\n".join(explanation_paragraphs)

    return RootCauseInvestigationResponse(
        request=request,
        summary=summary,
        decomposition=decomposition,
        ranked_contributors=all_ranked_contributors[: request.max_results],
        operational_indicators=op_indicators,
        explanation=explanation,
        limitations=STANDARD_LIMITATION,
    )
