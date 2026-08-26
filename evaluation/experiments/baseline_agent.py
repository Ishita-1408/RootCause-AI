"""Isolated Historical Baseline Investigation Agent Adapter.

Reconstructs documented Phase B / Phase G baseline behavior for controlled
scientific comparison without modifying production code:
1. Conflates "where" (segments) with "why" (causal mechanisms).
2. Lacks operational causal mechanism candidate generation on delivery metrics.
3. Ranks candidates purely by absolute volume magnitude.
4. Generates unconstrained legacy natural language findings (e.g. variance %
   rendered as shifted growth %, double-scaled rates).
5. Does not run the Phase H Claim Verification Firewall.
"""

from typing import Any, Literal

import psycopg

from apps.analytics.agent.executor import execute_investigation_steps
from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
    InvestigationState,
    RankedRootCause,
)
from apps.analytics.agent.planner import generate_initial_plan
from apps.analytics.agent.policies import should_terminate
from apps.analytics.rootcause.models import (
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)


def _rank_baseline_evidence(
    contributors: list[DimensionContributor],
    decomposition: VolumeValueDecomposition | None,
    operational_signals: OperationalIndicators | None,
    target_metric: str,
    max_causes: int = 5,
) -> list[RankedRootCause]:
    """Reconstruct Phase B legacy ranking without causal separation."""
    candidates: list[RankedRootCause] = []

    # 1. Decomposition candidates (unconstrained scoring by absolute effect)
    if decomposition and target_metric in {
        "total_gmv",
        "orders_count",
        "average_order_value",
    }:
        vol_pct = decomposition.volume_contribution_pct or 0.0
        vol_eff = decomposition.volume_effect
        if abs(vol_pct) >= 15.0:
            candidates.append(
                RankedRootCause(
                    rank=0,
                    title="Order Volume Shift",
                    dimension="order_volume",
                    dimension_value=f"{decomposition.observed_orders:,.0f} orders",
                    contribution_pct=round(vol_pct, 1),
                    absolute_change=round(vol_eff, 2),
                    score=abs(vol_eff),
                    explanation=f"Order volume shifted {vol_pct:+.1f}%.",
                    causal_category="macro_driver",
                    causal_mechanism="order_volume",
                    evidence_chain=[
                        f"Order volume shifted {vol_pct:+.1f}% vs baseline.",
                        f"Volume explains {abs(vol_pct):.1f}% of variance.",
                    ],
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

        aov_pct = decomposition.aov_contribution_pct or 0.0
        aov_eff = decomposition.aov_effect
        if abs(aov_pct) >= 15.0:
            candidates.append(
                RankedRootCause(
                    rank=0,
                    title="Average Order Value Shift",
                    dimension="average_order_value",
                    dimension_value=f"R$ {decomposition.observed_aov:.2f}",
                    contribution_pct=round(aov_pct, 1),
                    absolute_change=round(aov_eff, 2),
                    score=abs(aov_eff),
                    explanation=f"Average basket size shifted {aov_pct:+.1f}%.",
                    causal_category="macro_driver",
                    causal_mechanism="average_order_value",
                    evidence_chain=[
                        f"Average basket size shifted {aov_pct:+.1f}% vs baseline.",
                        f"Pricing explains {abs(aov_pct):.1f}% of variance.",
                    ],
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

    # 2. Dimensional Slices (Scored directly as root causes by absolute magnitude)
    for c in contributors:
        dim_label = c.dimension.replace("_", " ").title()
        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"{dim_label}: {c.dimension_value}",
                dimension=c.dimension,
                dimension_value=c.dimension_value,
                contribution_pct=round(c.contribution_pct or 0.0, 1),
                absolute_change=round(c.absolute_change, 2),
                score=abs(c.absolute_change),  # Pure magnitude ranking
                explanation=(
                    f"Segment slice '{c.dimension_value}' concentrated "
                    f"{c.contribution_pct or 0.0:+.1f}%."
                ),
                causal_category="segment_concentration",
                causal_mechanism=None,
                evidence_chain=[
                    f"Segment {c.dimension}: {c.dimension_value} evaluated.",
                    f"Observed R$ {c.observed_value:,.2f} vs baseline.",
                ],
                evidence_strength="high",
                confidence=0.95,
            )
        )

    # Sort all candidates purely by score (without causal mechanism prioritization)
    candidates.sort(key=lambda x: x.score, reverse=True)
    final_ranked = candidates[:max_causes]
    for idx, item in enumerate(final_ranked, start=1):
        item.rank = idx

    return final_ranked


def _generate_baseline_findings(
    summary: Any,
    decomposition: VolumeValueDecomposition | None,
    operational_signals: OperationalIndicators | None,
    top_causes: list[RankedRootCause],
) -> list[str]:
    """Reconstruct Phase G legacy unconstrained key findings."""
    findings: list[str] = []

    # Finding 1: Anomaly Summary
    pct_val = (
        f"{summary.percentage_change:+.1f}%"
        if summary.percentage_change is not None
        else "N/A"
    )
    findings.append(
        f"Headline {summary.metric} shifted {pct_val} on "
        f"{summary.anomaly_date} vs baseline."
    )

    # Finding 2: Decomposition (confused contribution % with growth %)
    if decomposition:
        vol_pct = decomposition.volume_contribution_pct or 0.0
        aov_pct = decomposition.aov_contribution_pct or 0.0
        if abs(vol_pct) >= abs(aov_pct):
            findings.append(
                f"Order volume shifted {vol_pct:+.1f}% vs 7-day rolling baseline."
            )
            findings.append(
                f"Volume change explains {abs(vol_pct):.1f}% of total "
                f"GMV variance (R$ {decomposition.volume_effect:+,.2f})."
            )
        else:
            findings.append(
                f"Average basket size shifted {aov_pct:+.1f}% vs "
                "7-day rolling baseline."
            )
            findings.append(
                f"Basket pricing explains {abs(aov_pct):.1f}% of total "
                f"GMV variance (R$ {decomposition.aov_effect:+,.2f})."
            )

    # Finding 3: Operational indicators (legacy double multiplication by 100)
    if operational_signals and (
        summary.metric in ("late_delivery_rate_pct", "delivery")
        or operational_signals.late_delivery_rate_change != 0
    ):
        obs_rate = operational_signals.observed_late_delivery_rate * 100.0
        base_rate = operational_signals.baseline_late_delivery_rate * 100.0
        findings.append(
            f"Late delivery rate rose to {obs_rate:.1f}% "
            f"(vs {base_rate:.1f}% baseline)."
        )

    # Add top cause explanations
    for c in top_causes:
        if len(findings) >= 4:
            break
        if c.explanation not in findings:
            findings.append(c.explanation)

    return findings[:4]


class BaselineInvestigationAgent:
    """Isolated adapter executing the Phase B / Phase G baseline behavior."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def run_investigation(
        self, request: InvestigationAgentRequest
    ) -> InvestigationAgentResponse:
        """Run baseline investigation without causal separation or claim firewall."""
        state = InvestigationState(
            metric=request.metric,
            anomaly_date=request.anomaly_date,
            max_steps=request.max_investigation_steps,
            minimum_contribution_pct=request.minimum_contribution_pct,
        )
        state.pending_steps = generate_initial_plan(request)

        # Execute analytical steps against DB
        rc_resp = execute_investigation_steps(
            conn=self.conn, request=request, state=state
        )

        # Baseline legacy ranking
        top_causes = _rank_baseline_evidence(
            contributors=rc_resp.ranked_contributors,
            decomposition=rc_resp.decomposition,
            operational_signals=rc_resp.operational_indicators,
            target_metric=request.metric,
            max_causes=5,
        )
        state.top_root_causes = top_causes

        # Termination policy
        is_term, term_reason = should_terminate(state)
        state.is_terminated = is_term
        state.termination_reason = (
            term_reason or "Investigation completed: All scheduled branches evaluated."
        )

        status_literal: Literal["completed", "early_terminated", "max_steps_reached"]
        if len(state.completed_steps) >= state.max_steps:
            status_literal = "max_steps_reached"
        else:
            status_literal = "completed"

        # Baseline legacy unconstrained findings without claim firewall
        key_findings = _generate_baseline_findings(
            summary=rc_resp.summary,
            decomposition=rc_resp.decomposition,
            operational_signals=rc_resp.operational_indicators,
            top_causes=top_causes,
        )

        return InvestigationAgentResponse(
            investigation_id=state.investigation_id,
            anomaly_summary=rc_resp.summary,
            investigation_status=status_literal,
            steps_executed=len(state.completed_steps),
            trace=state.completed_steps,
            decomposition=rc_resp.decomposition,
            top_root_causes=top_causes,
            supporting_evidence=rc_resp.ranked_contributors,
            operational_signals=rc_resp.operational_indicators,
            executive_summary=rc_resp.explanation,
            key_findings=key_findings,
            evidence_backed_claims=[],
            recommended_actions=[
                "Audit operational fulfillment buffers.",
                "Review pricing and promotions in leading categories.",
            ],
            limitations=rc_resp.limitations,
            termination_reason=state.termination_reason,
            model="baseline-heuristic-agent",
            is_fallback=True,
        )
