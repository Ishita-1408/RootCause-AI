"""Root-Cause Diagnostic Engine for RootCause AI.

Orchestrates multi-layer automated diagnostics:
1. Baseline & headline metric delta calculation
2. Mathematical Volume vs. AOV revenue decomposition
3. Dimensional slice attribution (Category, State, Seller, Tender)
4. Operational fulfillment performance signals
5. Customer satisfaction review signals
6. Multi-factor candidate root-cause scoring and ranking
"""

from datetime import timedelta
from typing import Any, Literal

import psycopg

from apps.analytics.diagnostics.models import (
    DiagnosticRequest,
    DiagnosticResponse,
    DiagnosticSummary,
    DimensionFinding,
    OperationalFinding,
    RevenueDecomposition,
    SatisfactionFinding,
)
from apps.analytics.diagnostics.queries import (
    fetch_dimension_slices_for_diagnostic,
    fetch_period_diagnostics,
)
from apps.analytics.diagnostics.scorers import (
    compute_root_cause_score,
    rank_candidate_root_causes,
)
from scripts.eda_helpers import format_currency_brl


def run_root_cause_analysis(
    conn: psycopg.Connection,
    request: DiagnosticRequest,
) -> DiagnosticResponse:
    """Execute complete multi-layer diagnostic investigation for an anomaly."""
    # 1. Calculate time windows
    actual_end = request.anomaly_date
    actual_start = actual_end - timedelta(days=request.comparison_window - 1)
    baseline_end = actual_start - timedelta(days=1)
    baseline_start = baseline_end - timedelta(days=request.baseline_window - 1)

    norm_factor = float(request.comparison_window) / float(request.baseline_window)

    # 2. Fetch raw period diagnostics
    cur_diag = fetch_period_diagnostics(
        conn=conn,
        start_date=actual_start,
        end_date=actual_end,
        category=request.category,
        customer_state=request.customer_state,
    )
    raw_base_diag = fetch_period_diagnostics(
        conn=conn,
        start_date=baseline_start,
        end_date=baseline_end,
        category=request.category,
        customer_state=request.customer_state,
    )

    # Normalize baseline additive metrics to comparison window equivalent
    base_orders = round(raw_base_diag["orders_count"] * norm_factor, 2)
    base_gmv = round(raw_base_diag["total_gmv"] * norm_factor, 2)
    base_aov = raw_base_diag["average_order_value"]
    base_late = raw_base_diag["late_delivery_rate_pct"]
    base_rev_score = raw_base_diag["avg_review_score"]

    cur_orders = cur_diag["orders_count"]
    cur_gmv = cur_diag["total_gmv"]
    cur_aov = cur_diag["average_order_value"]
    cur_late = cur_diag["late_delivery_rate_pct"]
    cur_rev_score = cur_diag["avg_review_score"]

    # Target metric selection
    if request.metric == "total_gmv":
        actual_val = cur_gmv
        base_val = base_gmv
    elif request.metric == "orders_count":
        actual_val = cur_orders
        base_val = base_orders
    elif request.metric == "average_order_value":
        actual_val = cur_aov
        base_val = base_aov
    elif request.metric == "late_delivery_rate_pct":
        actual_val = cur_late
        base_val = base_late
    elif request.metric == "avg_review_score":
        actual_val = cur_rev_score
        base_val = base_rev_score
    else:
        raise ValueError(f"Unsupported diagnostic metric: {request.metric}")

    abs_change = round(actual_val - base_val, 2)
    pct_change = round((abs_change / base_val) * 100.0, 2) if base_val > 0 else None

    # 3. Revenue Decomposition (Volume vs. AOV)
    rev_decomp: RevenueDecomposition | None = None
    delta_v = cur_orders - base_orders
    delta_a = cur_aov - base_aov
    vol_effect = round(delta_v * base_aov, 2)
    aov_effect = round(base_orders * delta_a, 2)
    interaction_effect = round(delta_v * delta_a, 2)
    total_rev_change = round(cur_gmv - base_gmv, 2)

    vol_contrib_pct = (
        round((vol_effect / total_rev_change) * 100.0, 2)
        if total_rev_change != 0
        else None
    )
    aov_contrib_pct = (
        round((aov_effect / total_rev_change) * 100.0, 2)
        if total_rev_change != 0
        else None
    )
    inter_contrib_pct = (
        round((interaction_effect / total_rev_change) * 100.0, 2)
        if total_rev_change != 0
        else None
    )

    rev_decomp = RevenueDecomposition(
        volume_effect=vol_effect,
        aov_effect=aov_effect,
        interaction_effect=interaction_effect,
        total_revenue_change=total_rev_change,
        volume_contribution_pct=vol_contrib_pct,
        aov_contribution_pct=aov_contrib_pct,
        interaction_contribution_pct=inter_contrib_pct,
    )

    # Primary Driver classification
    primary_driver: Literal[
        "ORDER_VOLUME",
        "AVERAGE_ORDER_VALUE",
        "FULFILLMENT_PERFORMANCE",
        "CUSTOMER_SATISFACTION",
        "STABLE_OR_BALANCED",
    ] = "STABLE_OR_BALANCED"

    if request.metric in ["total_gmv", "orders_count", "average_order_value"]:
        if abs(vol_effect) > abs(aov_effect):
            primary_driver = "ORDER_VOLUME"
        elif abs(aov_effect) > abs(vol_effect):
            primary_driver = "AVERAGE_ORDER_VALUE"
    elif request.metric == "late_delivery_rate_pct":
        primary_driver = "FULFILLMENT_PERFORMANCE"
    elif request.metric == "avg_review_score":
        primary_driver = "CUSTOMER_SATISFACTION"

    confidence_score = 0.85

    summary = DiagnosticSummary(
        metric=request.metric,
        anomaly_date=request.anomaly_date,
        comparison_period_start=actual_start,
        comparison_period_end=actual_end,
        baseline_period_start=baseline_start,
        baseline_period_end=baseline_end,
        actual_value=actual_val,
        baseline_value=base_val,
        absolute_change=abs_change,
        percentage_change=pct_change,
        primary_driver=primary_driver,
        confidence_score=confidence_score,
    )

    # 4. Dimensional Drill-Down
    dimensions = [
        "product_category_name",
        "customer_state",
        "seller_id",
        "payment_type",
    ]
    all_dim_findings: list[DimensionFinding] = []

    for dim in dimensions:
        slices = fetch_dimension_slices_for_diagnostic(
            conn=conn,
            dimension=dim,
            metric="total_gmv",
            actual_start=actual_start,
            actual_end=actual_end,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            norm_factor=norm_factor,
        )

        dim_entries: list[dict[str, Any]] = []
        for s in slices:
            act_s = s["actual_value"]
            base_s = s["baseline_value"]
            diff_s = round(act_s - base_s, 2)
            pct_s = round((diff_s / base_s) * 100.0, 2) if base_s > 0 else 100.0
            c_pct = (
                round((diff_s / total_rev_change) * 100.0, 2)
                if total_rev_change != 0
                else None
            )

            dim_entries.append(
                {
                    "dimension": dim,
                    "dimension_value": s["slice_value"],
                    "actual_value": act_s,
                    "baseline_value": base_s,
                    "change": diff_s,
                    "percentage_change": pct_s,
                    "contribution_pct": c_pct,
                }
            )

        # Sort by absolute magnitude of change descending
        dim_entries.sort(key=lambda x: abs(x["change"]), reverse=True)

        for rank_i, entry in enumerate(dim_entries[:3], start=1):
            all_dim_findings.append(
                DimensionFinding(
                    dimension=entry["dimension"],
                    dimension_value=entry["dimension_value"],
                    actual_value=entry["actual_value"],
                    baseline_value=entry["baseline_value"],
                    change=entry["change"],
                    percentage_change=entry["percentage_change"],
                    contribution_pct=entry["contribution_pct"],
                    rank=rank_i,
                )
            )

    # 5. Operational Signals
    op_signals: list[OperationalFinding] = []
    # Late delivery rate
    late_diff = round(cur_late - base_late, 2)
    late_pct = round((late_diff / base_late) * 100.0, 2) if base_late > 0 else 0.0
    late_sev: Literal["normal", "warning", "critical"] = "normal"
    if cur_late >= 15.0 or late_diff >= 5.0:
        late_sev = "critical"
    elif cur_late >= 10.0 or late_diff >= 2.0:
        late_sev = "warning"

    op_signals.append(
        OperationalFinding(
            metric="late_delivery_rate_pct",
            actual_value=cur_late,
            baseline_value=base_late,
            change=late_diff,
            percentage_change=late_pct,
            severity=late_sev,
        )
    )

    # Carrier transit days
    cur_transit = cur_diag["carrier_transit_days"]
    base_transit = raw_base_diag["carrier_transit_days"]
    transit_diff = round(cur_transit - base_transit, 2)
    transit_pct = (
        round((transit_diff / base_transit) * 100.0, 2) if base_transit > 0 else 0.0
    )
    transit_sev: Literal["normal", "warning", "critical"] = (
        "warning" if transit_diff >= 3.0 else "normal"
    )
    op_signals.append(
        OperationalFinding(
            metric="carrier_transit_days",
            actual_value=cur_transit,
            baseline_value=base_transit,
            change=transit_diff,
            percentage_change=transit_pct,
            severity=transit_sev,
        )
    )

    # Cancellation rate
    cur_canc = cur_diag["cancellation_rate_pct"]
    base_canc = raw_base_diag["cancellation_rate_pct"]
    canc_diff = round(cur_canc - base_canc, 2)
    canc_pct = round((canc_diff / base_canc) * 100.0, 2) if base_canc > 0 else 0.0
    canc_sev: Literal["normal", "warning", "critical"] = (
        "warning" if canc_diff >= 1.0 else "normal"
    )
    op_signals.append(
        OperationalFinding(
            metric="cancellation_rate_pct",
            actual_value=cur_canc,
            baseline_value=base_canc,
            change=canc_diff,
            percentage_change=canc_pct,
            severity=canc_sev,
        )
    )

    # 6. Customer Satisfaction Signals
    sat_signals: list[SatisfactionFinding] = []
    rev_diff = round(cur_rev_score - base_rev_score, 2)
    rev_pct = (
        round((rev_diff / base_rev_score) * 100.0, 2) if base_rev_score > 0 else 0.0
    )
    rev_impact: Literal["positive", "neutral", "negative"] = "neutral"
    if rev_diff <= -0.3:
        rev_impact = "negative"
    elif rev_diff >= 0.3:
        rev_impact = "positive"

    sat_signals.append(
        SatisfactionFinding(
            metric="avg_review_score",
            actual_value=cur_rev_score,
            baseline_value=base_rev_score,
            change=rev_diff,
            percentage_change=rev_pct,
            sentiment_impact=rev_impact,
        )
    )

    # Negative review rate (1-2 stars)
    cur_neg_rev = cur_diag["negative_review_rate_pct"]
    base_neg_rev = raw_base_diag["negative_review_rate_pct"]
    neg_rev_diff = round(cur_neg_rev - base_neg_rev, 2)
    neg_rev_pct = (
        round((neg_rev_diff / base_neg_rev) * 100.0, 2) if base_neg_rev > 0 else 0.0
    )
    neg_rev_impact: Literal["positive", "neutral", "negative"] = (
        "negative" if neg_rev_diff >= 3.0 else "neutral"
    )

    sat_signals.append(
        SatisfactionFinding(
            metric="negative_review_rate_pct",
            actual_value=cur_neg_rev,
            baseline_value=base_neg_rev,
            change=neg_rev_diff,
            percentage_change=neg_rev_pct,
            sentiment_impact=neg_rev_impact,
        )
    )

    # 7. Candidate Root Causes Multi-Factor Scoring & Ranking
    candidates: list[dict[str, Any]] = []

    # Candidate A: Order Volume
    vol_mag = min(1.0, abs(delta_v) / (base_orders + 1e-5))
    vol_contrib_share = (
        min(1.0, abs(vol_effect) / (abs(total_rev_change) + 1e-5))
        if total_rev_change != 0
        else 0.0
    )
    candidates.append(
        {
            "cause": "Order volume shift",
            "category": "VOLUME",
            "score": compute_root_cause_score(
                magnitude=vol_mag, contribution=vol_contrib_share
            ),
            "contribution": f"{vol_contrib_pct:+.1f}% of total GMV movement"
            if vol_contrib_pct is not None
            else "N/A",
            "evidence": (
                f"Orders shifted by {delta_v:+,.0f} orders ({cur_orders:,.0f} "
                f"vs {base_orders:,.0f} baseline), driving "
                f"{format_currency_brl(vol_effect)} effect."
            ),
        }
    )

    # Candidate B: Pricing / AOV
    aov_mag = min(1.0, abs(delta_a) / (base_aov + 1e-5))
    aov_contrib_share = (
        min(1.0, abs(aov_effect) / (abs(total_rev_change) + 1e-5))
        if total_rev_change != 0
        else 0.0
    )
    candidates.append(
        {
            "cause": "Average Order Value (AOV) shift",
            "category": "PRICING_AOV",
            "score": compute_root_cause_score(
                magnitude=aov_mag, contribution=aov_contrib_share
            ),
            "contribution": f"{aov_contrib_pct:+.1f}% of total GMV movement"
            if aov_contrib_pct is not None
            else "N/A",
            "evidence": (
                f"AOV changed by {format_currency_brl(delta_a)} "
                f"({format_currency_brl(cur_aov)} vs {format_currency_brl(base_aov)} "
                f"baseline), driving {format_currency_brl(aov_effect)} effect."
            ),
        }
    )

    # Candidate C: Top category slice
    top_cat = next(
        (f for f in all_dim_findings if f.dimension == "product_category_name"),
        None,
    )
    if top_cat:
        cat_mag = min(1.0, abs(top_cat.change) / (abs(top_cat.baseline_value) + 1e-5))
        cat_contrib_share = (
            min(1.0, abs(top_cat.change) / (abs(total_rev_change) + 1e-5))
            if total_rev_change != 0
            else 0.0
        )
        candidates.append(
            {
                "cause": f"Category concentration: {top_cat.dimension_value}",
                "category": "DIMENSION_CONCENTRATION",
                "score": compute_root_cause_score(
                    magnitude=cat_mag, contribution=cat_contrib_share
                ),
                "contribution": f"{top_cat.contribution_pct:+.1f}% share"
                if top_cat.contribution_pct is not None
                else "N/A",
                "evidence": (
                    f"Category '{top_cat.dimension_value}' delta of "
                    f"{format_currency_brl(top_cat.change)} "
                    f"({format_currency_brl(top_cat.actual_value)} vs "
                    f"{format_currency_brl(top_cat.baseline_value)})."
                ),
            }
        )

    # Candidate D: Operational Delivery Signal
    if late_sev in ["warning", "critical"]:
        op_mag = min(1.0, abs(late_diff) / (base_late + 1e-5))
        candidates.append(
            {
                "cause": "Late delivery rate escalation",
                "category": "OPERATIONAL_FULFILLMENT",
                "score": compute_root_cause_score(
                    magnitude=op_mag, contribution=0.35, consistency=0.9
                ),
                "contribution": "Supporting operational factor",
                "evidence": (
                    f"Late delivery rate deteriorated from {base_late:.1f}% "
                    f"to {cur_late:.1f}% (+{late_diff:.1f}pp)."
                ),
            }
        )

    ranked_root_causes = rank_candidate_root_causes(candidates)

    # 8. Formulate Conclusion
    top_driver_desc = "lower order volume" if vol_effect < 0 else "higher order volume"
    if primary_driver == "AVERAGE_ORDER_VALUE":
        top_driver_desc = (
            "lower basket size (AOV)" if aov_effect < 0 else "higher basket size (AOV)"
        )

    pct_str = f"{pct_change:+.1f}%" if pct_change is not None else "N/A"
    conclusion = (
        f"The primary driver of the {request.metric.upper()} movement "
        f"({pct_str}) was {top_driver_desc}, explaining "
        f"{vol_contrib_pct if primary_driver == 'ORDER_VOLUME' else aov_contrib_pct}% "
        f"of total variance. "
    )
    if top_cat:
        cat_delta_str = format_currency_brl(top_cat.change)
        conclusion += (
            f"The highest contributing category was "
            f"'{top_cat.dimension_value}' ({cat_delta_str}). "
        )
    if late_sev in ["warning", "critical"]:
        conclusion += (
            f"Delivery fulfillment showed operational deterioration "
            f"({base_late:.1f}% -> {cur_late:.1f}% late rate)."
        )

    return DiagnosticResponse(
        request=request,
        summary=summary,
        revenue_decomposition=rev_decomp,
        top_dimensional_contributors=all_dim_findings,
        operational_signals=op_signals,
        satisfaction_signals=sat_signals,
        root_cause_ranking=ranked_root_causes,
        conclusion=conclusion,
    )
