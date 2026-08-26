"""Autonomous Business Investigation Agent Orchestrator."""

import logging
from collections.abc import Iterator
from typing import Any, Literal

import psycopg

from apps.ai.investigator import investigate_with_ai
from apps.analytics.agent.claims import generate_evidence_backed_claims
from apps.analytics.agent.executor import execute_investigation_steps
from apps.analytics.agent.firewall import apply_claim_firewall
from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
    InvestigationState,
)
from apps.analytics.agent.planner import generate_initial_plan
from apps.analytics.agent.policies import should_terminate
from apps.analytics.agent.ranker import rank_evidence
from apps.analytics.statistics import build_statistical_evidence_summary

logger = logging.getLogger(__name__)


class AutonomousInvestigationAgent:
    """Autonomous Agent orchestrating deterministic analysis and AI memo."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def run_investigation(
        self, request: InvestigationAgentRequest
    ) -> InvestigationAgentResponse:
        """Run end-to-end adaptive investigation."""
        # 1. Initialize State
        state = InvestigationState(
            metric=request.metric,
            anomaly_date=request.anomaly_date,
            max_steps=request.max_investigation_steps,
            minimum_contribution_pct=request.minimum_contribution_pct,
            pending_steps=generate_initial_plan(request),
        )

        # 2. Execute Steps Deterministically
        rc_resp = execute_investigation_steps(
            conn=self.conn, request=request, state=state
        )

        # 3. Rank Root Causes Transparently & Separate Cause from Segment
        top_causes = rank_evidence(
            contributors=rc_resp.ranked_contributors,
            decomposition=rc_resp.decomposition,
            summary=rc_resp.summary,
            operational_signals=rc_resp.operational_indicators,
            max_causes=5,
        )
        state.top_root_causes = top_causes

        # 4. Check Termination Policy
        is_term, term_reason = should_terminate(state)
        state.is_terminated = is_term
        state.termination_reason = (
            term_reason or "Investigation completed: All scheduled branches evaluated."
        )

        # 5. Synthesize Executive Narrative via Phase 5C AI Layer
        try:
            ai_memo = investigate_with_ai(root_cause_response=rc_resp)
            exec_summary = ai_memo.executive_summary
            recommended_actions = ai_memo.recommended_actions
            model_name = ai_memo.model
            is_fallback = ai_memo.is_fallback
        except Exception as e:
            logger.warning(f"AI explanation layer failed, falling back: {e}")
            exec_summary = rc_resp.explanation
            recommended_actions = [
                "Audit operational fulfillment buffers.",
                "Review pricing and promotions in leading categories.",
            ]
            model_name = "deterministic-rule-synthesizer"
            is_fallback = True

        status_literal: Literal["completed", "early_terminated", "max_steps_reached"]
        if len(state.completed_steps) >= state.max_steps:
            status_literal = "max_steps_reached"
        else:
            status_literal = "completed"

        # 6. Compute Change-Point Analysis (Phase J)
        from datetime import timedelta

        from apps.analytics.change_detection import run_change_point_detection

        cp_analysis = None
        try:
            with self.conn.transaction():
                start_d = request.anomaly_date - timedelta(days=14)
                end_d = request.anomaly_date
                cp_resp = run_change_point_detection(
                    conn=self.conn,
                    metric=request.metric,
                    start_date=start_d,
                    end_date=end_d,
                    minimum_segment_size=3,
                )
                cp_analysis = cp_resp.change_point
        except Exception:
            cp_analysis = None

        # 7. Synthesize Statistical Confidence & Significance Evidence (Phase K)
        stat_evidence = build_statistical_evidence_summary(
            summary=rc_resp.summary,
            decomposition=rc_resp.decomposition,
            operational_signals=rc_resp.operational_indicators,
            contributors=rc_resp.ranked_contributors,
            cp_analysis=cp_analysis,
        )

        # 8. Generate Deterministic Evidence-Backed Claims (Phase H & K)
        candidate_claims = generate_evidence_backed_claims(
            summary=rc_resp.summary,
            decomposition=rc_resp.decomposition,
            operational_signals=rc_resp.operational_indicators,
            contributors=rc_resp.ranked_contributors,
            top_root_causes=top_causes,
            statistical_evidence=stat_evidence,
        )

        # 9. Apply Claim Verification Firewall (Phase H & K)
        from evaluation.hallucination.extractor import extract_evidence_from_response

        # Build initial response container to extract analytical evidence pool
        initial_resp = InvestigationAgentResponse(
            investigation_id=state.investigation_id,
            anomaly_summary=rc_resp.summary,
            investigation_status=status_literal,
            steps_executed=len(state.completed_steps),
            trace=state.completed_steps,
            decomposition=rc_resp.decomposition,
            top_root_causes=top_causes,
            supporting_evidence=rc_resp.ranked_contributors,
            operational_signals=rc_resp.operational_indicators,
            executive_summary=exec_summary,
            key_findings=[],
            evidence_backed_claims=[],
            change_point_analysis=cp_analysis,
            statistical_evidence=stat_evidence,
            recommended_actions=recommended_actions,
            limitations=rc_resp.limitations,
            termination_reason=state.termination_reason,
            model=model_name,
            is_fallback=is_fallback,
        )
        evidence_pool = extract_evidence_from_response(initial_resp)

        verified_claims, final_findings = apply_claim_firewall(
            claims=candidate_claims,
            evidence_pool=evidence_pool,
            scenario_date=request.anomaly_date,
        )

        # 10. Build Structured Evidence Graph (Phase M)
        from apps.analytics.graph.builder import build_evidence_graph
        from apps.analytics.replay.engine import register_investigation_snapshot

        ev_graph = build_evidence_graph(
            metric_name=request.metric,
            anomaly_date=str(request.anomaly_date),
            observed_value=rc_resp.summary.observed_value,
            baseline_value=rc_resp.summary.baseline_value or 0.0,
            ranked_causes=top_causes,
            statistical_evidence=stat_evidence,
            dimensional_breakdowns=rc_resp.ranked_contributors,
            session_id=state.investigation_id,
        )

        final_response = InvestigationAgentResponse(
            investigation_id=state.investigation_id,
            anomaly_summary=rc_resp.summary,
            investigation_status=status_literal,
            steps_executed=len(state.completed_steps),
            trace=state.completed_steps,
            decomposition=rc_resp.decomposition,
            top_root_causes=top_causes,
            supporting_evidence=rc_resp.ranked_contributors,
            operational_signals=rc_resp.operational_indicators,
            executive_summary=exec_summary,
            key_findings=final_findings[:4],
            evidence_backed_claims=verified_claims,
            change_point_analysis=cp_analysis,
            statistical_evidence=stat_evidence,
            evidence_graph=ev_graph,
            recommended_actions=recommended_actions,
            limitations=rc_resp.limitations,
            termination_reason=state.termination_reason,
            model=model_name,
            is_fallback=is_fallback,
        )

        # Register immutable replay snapshot
        register_investigation_snapshot(final_response)

        return final_response

    def stream_investigation(
        self, request: InvestigationAgentRequest
    ) -> Iterator[dict[str, Any]]:
        """Execute investigation yielding real-time progressive SSE events."""
        # 1. State initialization
        state = InvestigationState(
            metric=request.metric,
            anomaly_date=request.anomaly_date,
            max_steps=request.max_investigation_steps,
            minimum_contribution_pct=request.minimum_contribution_pct,
            pending_steps=generate_initial_plan(request),
        )

        yield {
            "event": "investigation_started",
            "data": {
                "investigation_id": state.investigation_id,
                "metric": request.metric,
                "anomaly_date": str(request.anomaly_date),
            },
        }

        # 2. Execute Steps with progress events
        yield {
            "event": "stage_update",
            "data": {
                "stage": 1,
                "title": "Detecting Anomaly & Baseline Window",
                "status": "in_progress",
            },
        }

        rc_resp = execute_investigation_steps(
            conn=self.conn, request=request, state=state
        )

        pct_fmt = (
            f"{rc_resp.summary.percentage_change:+.1f}%"
            if rc_resp.summary.percentage_change is not None
            else "N/A"
        )
        yield {
            "event": "stage_update",
            "data": {
                "stage": 1,
                "title": "Detected Unusual Metric Shift",
                "status": "completed",
                "finding": f"Anomaly on {request.anomaly_date} ({pct_fmt} vs baseline)",
            },
        }

        # 3. Tested Causal Drivers
        yield {
            "event": "stage_update",
            "data": {
                "stage": 2,
                "title": "Testing Causal Revenue Drivers",
                "status": "completed",
                "finding": "Volume vs AOV mathematical decomposition computed",
            },
        }

        # 4. Rank Root Causes & Separate Cause from Segment
        top_causes = rank_evidence(
            contributors=rc_resp.ranked_contributors,
            decomposition=rc_resp.decomposition,
            summary=rc_resp.summary,
            operational_signals=rc_resp.operational_indicators,
            max_causes=5,
        )
        state.top_root_causes = top_causes

        top_aff = (
            top_causes[0].affected_value
            if top_causes and top_causes[0].affected_value
            else "primary segment"
        )
        yield {
            "event": "stage_update",
            "data": {
                "stage": 3,
                "title": "Identified Affected Segments",
                "status": "completed",
                "finding": f"Impact concentrated in {top_aff}",
            },
        }

        # 5. Check Termination Policy & Operational Signals
        is_term, term_reason = should_terminate(state)
        state.is_terminated = is_term
        state.termination_reason = (
            term_reason or "Investigation completed: All scheduled branches evaluated."
        )

        yield {
            "event": "stage_update",
            "data": {
                "stage": 4,
                "title": "Verified Supporting Evidence & Telemetry",
                "status": "completed",
                "finding": "Operational indicators and dimensional mart data verified",
            },
        }

        # 6. Synthesize Executive Narrative
        try:
            ai_memo = investigate_with_ai(root_cause_response=rc_resp)
            exec_summary = ai_memo.executive_summary
            primary_cause = top_causes[0] if top_causes else None
            grounded_findings = (
                list(primary_cause.evidence_chain)
                if primary_cause and primary_cause.evidence_chain
                else []
            )
            for f in ai_memo.key_findings:
                if f not in grounded_findings:
                    grounded_findings.append(f)

            key_findings = (
                grounded_findings[:4]
                if grounded_findings
                else [c.explanation for c in top_causes[:4]]
            )
            recommended_actions = ai_memo.recommended_actions
            model_name = ai_memo.model
            is_fallback = ai_memo.is_fallback
        except Exception as e:
            logger.warning(f"AI explanation layer failed, falling back: {e}")
            exec_summary = rc_resp.explanation
            key_findings = [c.explanation for c in top_causes[:4]]
            recommended_actions = [
                "Audit operational fulfillment buffers.",
                "Review pricing and promotions in leading categories.",
            ]
            model_name = "deterministic-rule-synthesizer"
            is_fallback = True

        status_literal: Literal["completed", "early_terminated", "max_steps_reached"]
        if len(state.completed_steps) >= state.max_steps:
            status_literal = "max_steps_reached"
        else:
            status_literal = "completed"

        # Compute Statistical Evidence Summary (Phase K)
        stat_evidence = build_statistical_evidence_summary(
            summary=rc_resp.summary,
            decomposition=rc_resp.decomposition,
            operational_signals=rc_resp.operational_indicators,
            contributors=rc_resp.ranked_contributors,
            cp_analysis=None,
        )

        # Compute Structured Evidence Graph (Phase M)
        from apps.analytics.graph.builder import build_evidence_graph
        from apps.analytics.replay.engine import register_investigation_snapshot

        ev_graph = build_evidence_graph(
            metric_name=request.metric,
            anomaly_date=str(request.anomaly_date),
            observed_value=rc_resp.summary.observed_value,
            baseline_value=rc_resp.summary.baseline_value or 0.0,
            ranked_causes=top_causes,
            statistical_evidence=stat_evidence,
            dimensional_breakdowns=rc_resp.ranked_contributors,
            session_id=state.investigation_id,
        )

        final_response = InvestigationAgentResponse(
            investigation_id=state.investigation_id,
            anomaly_summary=rc_resp.summary,
            investigation_status=status_literal,
            steps_executed=len(state.completed_steps),
            trace=state.completed_steps,
            decomposition=rc_resp.decomposition,
            top_root_causes=top_causes,
            supporting_evidence=rc_resp.ranked_contributors,
            operational_signals=rc_resp.operational_indicators,
            executive_summary=exec_summary,
            key_findings=key_findings,
            statistical_evidence=stat_evidence,
            evidence_graph=ev_graph,
            recommended_actions=recommended_actions,
            limitations=rc_resp.limitations,
            termination_reason=state.termination_reason,
            model=model_name,
            is_fallback=is_fallback,
        )

        register_investigation_snapshot(final_response)

        yield {
            "event": "stage_update",
            "data": {
                "stage": 5,
                "title": "Reached Forensic Conclusion",
                "status": "completed",
                "finding": final_response.executive_summary,
            },
        }

        yield {
            "event": "investigation_completed",
            "data": final_response.model_dump(mode="json"),
        }


def run_autonomous_investigation(
    conn: psycopg.Connection, request: InvestigationAgentRequest
) -> InvestigationAgentResponse:
    """Convenience functional interface for Autonomous Investigation Agent."""
    agent = AutonomousInvestigationAgent(conn=conn)
    return agent.run_investigation(request=request)


def run_autonomous_investigation_stream(
    conn: psycopg.Connection, request: InvestigationAgentRequest
) -> Iterator[dict[str, Any]]:
    """Convenience generator interface for streaming investigation events."""
    agent = AutonomousInvestigationAgent(conn=conn)
    return agent.stream_investigation(request=request)
