"""Unit and Integration Tests for Evidence Graph, Replay, and Challenge (Phase M)."""

from datetime import date

from apps.analytics.agent.models import (
    InvestigationStepTrace,
    RankedRootCause,
)
from apps.analytics.challenge import ChallengeRequest, evaluate_challenge
from apps.analytics.graph import build_evidence_graph
from apps.analytics.replay import (
    get_investigation_snapshot,
    list_recent_snapshots,
    register_investigation_snapshot,
)


def test_build_evidence_graph_structure() -> None:
    """Verify that build_evidence_graph creates a valid 7-tier DAG."""
    causes = [
        RankedRootCause(
            rank=1,
            title="Order Volume Contraction",
            dimension="customer_state",
            dimension_value="SP",
            contribution_pct=88.5,
            absolute_change=-12000.0,
            score=95.0,
            explanation="Order volume dropped by 32 orders.",
            causal_mechanism="order_volume",
            affected_dimension="customer_state",
            affected_value="SP",
        )
    ]

    graph = build_evidence_graph(
        metric_name="total_gmv",
        anomaly_date="2017-11-20",
        observed_value=22410.0,
        baseline_value=31300.0,
        ranked_causes=causes,
        session_id="test_session_123",
    )

    assert graph.graph_id == "test_session_123"
    assert len(graph.nodes) == 7
    assert len(graph.edges) == 6
    assert len(graph.primary_chain_node_ids) == 7

    node_types = [n.node_type for n in graph.nodes]
    assert node_types == [
        "INCIDENT",
        "ANOMALY",
        "DRIVER",
        "EVIDENCE",
        "SEGMENT",
        "CORROBORATION",
        "ROOT_CAUSE",
    ]


def test_evidence_graph_dag_acyclicity() -> None:
    """Verify graph is strictly a Directed Acyclic Graph (no loops)."""
    causes = [
        RankedRootCause(
            rank=1,
            title="AOV Contraction",
            dimension="payment_type",
            dimension_value="credit_card",
            contribution_pct=75.0,
            absolute_change=-5000.0,
            score=88.0,
            explanation="AOV dropped.",
            causal_mechanism="average_order_value",
        )
    ]
    graph = build_evidence_graph(
        metric_name="total_gmv",
        anomaly_date="2017-11-20",
        observed_value=15000.0,
        baseline_value=20000.0,
        ranked_causes=causes,
    )

    node_ids = {n.node_id for n in graph.nodes}
    for e in graph.edges:
        assert e.source_id in node_ids
        assert e.target_id in node_ids
        assert e.source_id != e.target_id


def test_register_and_retrieve_investigation_snapshot() -> None:
    """Verify investigation snapshot persistence and retrieval."""
    from apps.analytics.agent.models import (
        AnomalySummary,
        InvestigationAgentResponse,
        OperationalIndicators,
    )

    resp = InvestigationAgentResponse(
        investigation_id="session_test_snapshot_456",
        anomaly_summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 20),
            baseline_start_date=date(2017, 11, 13),
            baseline_end_date=date(2017, 11, 19),
            observed_value=22000.0,
            baseline_value=30000.0,
            absolute_change=-8000.0,
            percentage_change=-26.7,
            direction="decrease",
        ),
        investigation_status="completed",
        steps_executed=4,
        trace=[
            InvestigationStepTrace(
                step_number=1,
                step_type="ANOMALY_DETECTION",
                step_title="Anomaly Checked",
                status="completed",
            )
        ],
        top_root_causes=[],
        supporting_evidence=[],
        operational_signals=OperationalIndicators(
            observed_late_delivery_rate=0.08,
            baseline_late_delivery_rate=0.04,
            late_delivery_rate_change=0.04,
            observed_avg_delivery_days=12.5,
            baseline_avg_delivery_days=10.0,
            avg_delivery_days_change=2.5,
            observed_cancellation_rate=0.01,
            baseline_cancellation_rate=0.01,
            cancellation_rate_change=0.0,
            observed_avg_review_score=4.2,
            baseline_avg_review_score=4.5,
            avg_review_score_change=-0.3,
        ),
        executive_summary="Summary of findings.",
        key_findings=["Finding 1"],
        recommended_actions=["Action 1"],
        limitations="None",
        termination_reason="Completed",
        model="deterministic_engine",
        is_fallback=False,
    )

    snapshot = register_investigation_snapshot(resp)
    assert snapshot.session_id == "session_test_snapshot_456"
    assert snapshot.total_steps == 1

    retrieved = get_investigation_snapshot("session_test_snapshot_456")
    assert retrieved is not None
    assert retrieved.session_id == "session_test_snapshot_456"

    recent = list_recent_snapshots(limit=10)
    assert any(s["session_id"] == "session_test_snapshot_456" for s in recent)


def test_challenge_mode_all_types() -> None:
    """Verify challenge mode questions are evaluated deterministically."""
    # 1. Why not cause
    req1 = ChallengeRequest(
        session_id="session_test_snapshot_456",
        challenge_type="why_not_cause",
        candidate_cause="average_order_value",
    )
    res1 = evaluate_challenge(req1)
    q1 = res1.challenge_question.lower()
    assert "rejected" in q1 or "why was" in q1
    assert len(res1.evaluations) >= 1

    # 2. Contradicting evidence
    req2 = ChallengeRequest(
        session_id="session_test_snapshot_456",
        challenge_type="contradicting_evidence",
    )
    res2 = evaluate_challenge(req2)
    assert "contradicts" in res2.challenge_question.lower()
    assert len(res2.evaluations) >= 1

    # 3. Weakest link
    req3 = ChallengeRequest(
        session_id="session_test_snapshot_456",
        challenge_type="weakest_link",
    )
    res3 = evaluate_challenge(req3)
    assert "weakest" in res3.challenge_question.lower()
    assert len(res3.evaluations) >= 1

    # 4. What would change
    req4 = ChallengeRequest(
        session_id="session_test_snapshot_456",
        challenge_type="what_would_change",
    )
    res4 = evaluate_challenge(req4)
    assert "change" in res4.challenge_question.lower()
    assert len(res4.evaluations) >= 1
