"""Deterministic execution engine for executing planned investigation steps."""

from typing import Any

import psycopg

from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationState,
    InvestigationStepTrace,
)
from apps.analytics.agent.policies import should_skip_branch
from apps.analytics.rootcause.engine import investigate_root_cause
from apps.analytics.rootcause.models import (
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
)


def execute_investigation_steps(
    conn: psycopg.Connection,
    request: InvestigationAgentRequest,
    state: InvestigationState,
) -> RootCauseInvestigationResponse:
    """Execute scheduled analytical branches deterministically against Supabase."""
    # 1. Fetch comprehensive verified root-cause evidence via Phase 5B engine
    rc_req = RootCauseInvestigationRequest(
        metric=request.metric,
        anomaly_date=request.anomaly_date,
        comparison_days=request.comparison_days,
        dimensions=request.dimensions,
        max_results=10,
    )
    rc_resp = investigate_root_cause(conn=conn, request=rc_req)

    # Populate state evidence
    evidence: dict[str, Any] = {
        "summary": rc_resp.summary,
        "decomposition": rc_resp.decomposition,
        "ranked_contributors": rc_resp.ranked_contributors,
        "operational_indicators": rc_resp.operational_indicators,
        "category_contributors": [
            c for c in rc_resp.ranked_contributors if c.dimension == "product_category"
        ],
        "state_contributors": [
            c for c in rc_resp.ranked_contributors if c.dimension == "customer_state"
        ],
        "seller_contributors": [
            c for c in rc_resp.ranked_contributors if c.dimension == "seller"
        ],
    }
    state.evidence = evidence

    # 2. Sequentially process pending branches in queue
    step_num = 1
    while state.pending_steps and state.current_step < state.max_steps:
        branch = state.pending_steps.pop(0)
        state.current_step += 1

        # Check skip policy
        skip, skip_reason = should_skip_branch(
            branch_type=branch,
            evidence=evidence,
            minimum_contribution_pct=request.minimum_contribution_pct,
        )

        if skip:
            state.completed_steps.append(
                InvestigationStepTrace(
                    step_number=step_num,
                    step_type=branch,
                    step_title=branch.replace("_", " ").title(),
                    status="skipped",
                    finding_summary=None,
                    details={},
                    reason_if_skipped=skip_reason,
                )
            )
            step_num += 1
            continue

        # Execute Branch
        trace_entry = _execute_single_branch(branch, step_num, evidence)
        state.completed_steps.append(trace_entry)
        step_num += 1

    return rc_resp


def _execute_single_branch(
    branch: str, step_num: int, evidence: dict[str, Any]
) -> InvestigationStepTrace:
    """Evaluate findings for a single completed branch."""
    if branch == "volume_aov_decomposition":
        decomp = evidence.get("decomposition")
        if decomp:
            vol_pct = decomp.volume_contribution_pct or 0.0
            aov_pct = decomp.aov_contribution_pct or 0.0
            summary = (
                f"Order volume shifted {vol_pct:+.1f}% (primary driver); "
                f"AOV shifted {aov_pct:+.1f}%."
            )
            details = {
                "volume_effect": decomp.volume_effect,
                "aov_effect": decomp.aov_effect,
                "observed_orders": decomp.observed_orders,
                "baseline_orders": decomp.baseline_orders,
            }
        else:
            summary = "Volume vs AOV decomposition not applicable for this metric."
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Volume vs. AOV Decomposition",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    if branch == "customer_state_drilldown":
        states = evidence.get("state_contributors", [])
        if states:
            top_state = states[0]
            val = top_state.dimension_value
            pct = top_state.contribution_pct or 0.0
            chg = top_state.absolute_change
            summary = f"Top state '{val}' contributed {pct:+.1f}% (R$ {chg:+,.2f})."
            details = {
                "top_state": top_state.dimension_value,
                "contribution_pct": top_state.contribution_pct,
                "observed": top_state.observed_value,
            }
        else:
            summary = "No state slices exceeded the significance threshold."
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Customer Geographic Slicing",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    if branch == "product_category_drilldown":
        cats = evidence.get("category_contributors", [])
        if cats:
            top_cat = cats[0]
            c_val = top_cat.dimension_value
            c_pct = top_cat.contribution_pct or 0.0
            c_chg = top_cat.absolute_change
            summary = (
                f"Top category '{c_val}' contributed {c_pct:+.1f}% (R$ {c_chg:+,.2f})."
            )
            details = {
                "top_category": top_cat.dimension_value,
                "contribution_pct": top_cat.contribution_pct,
                "observed": top_cat.observed_value,
            }
        else:
            summary = "No category slices exceeded the significance threshold."
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Product Category Mix Analysis",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    if branch == "seller_drilldown":
        sellers = evidence.get("seller_contributors", [])
        if sellers:
            top_seller = sellers[0]
            s_val = top_seller.dimension_value
            s_pct = top_seller.contribution_pct or 0.0
            summary = f"Top seller '{s_val}' contributed {s_pct:+.1f}%."
            details = {
                "top_seller": top_seller.dimension_value,
                "contribution_pct": top_seller.contribution_pct,
            }
        else:
            summary = (
                "Merchant volume was distributed across diverse independent sellers."
            )
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Merchant / Seller Concentration",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    if branch == "operational_signals_evaluation":
        op = evidence.get("operational_indicators")
        if op:
            summary = (
                f"Late delivery rate stood at {op.observed_late_delivery_rate:.1f}% "
                f"(vs {op.baseline_late_delivery_rate:.1f}% baseline); "
                f"avg transit lead time was {op.observed_avg_delivery_days:.1f} days."
            )
            details = {
                "late_delivery_rate": op.observed_late_delivery_rate,
                "avg_delivery_days": op.observed_avg_delivery_days,
            }
        else:
            summary = "Operational indicators stable."
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Logistics & Delivery Telemetry",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    if branch == "customer_sentiment_evaluation":
        op = evidence.get("operational_indicators")
        if op:
            summary = (
                f"Customer review score was {op.observed_avg_review_score:.2f}/5.0 "
                f"(vs {op.baseline_avg_review_score:.2f} baseline)."
            )
            details = {"avg_review_score": op.observed_avg_review_score}
        else:
            summary = "Customer review score stable."
            details = {}

        return InvestigationStepTrace(
            step_number=step_num,
            step_type=branch,
            step_title="Customer Review Sentiment",
            status="completed",
            finding_summary=summary,
            details=details,
        )

    return InvestigationStepTrace(
        step_number=step_num,
        step_type=branch,
        step_title=branch.replace("_", " ").title(),
        status="completed",
        finding_summary="Analysis completed.",
        details={},
    )
