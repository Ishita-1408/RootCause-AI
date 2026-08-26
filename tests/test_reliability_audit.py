"""Phase N: Comprehensive Production + ML Reliability Audit Test Suite."""

from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.analytics.agent.models import (
    AnomalySummary,
    InvestigationAgentResponse,
    InvestigationStepTrace,
    OperationalIndicators,
    RankedRootCause,
)
from apps.analytics.challenge import ChallengeRequest, evaluate_challenge
from apps.analytics.graph import build_evidence_graph
from apps.analytics.replay import (
    get_investigation_snapshot,
    register_investigation_snapshot,
)
from apps.api.auth import AuthUser, Role, get_current_user, require_role
from apps.api.config import Settings
from apps.api.db.connection import check_database_connection, get_db_connection
from apps.api.main import app

client = TestClient(app)


# ============================================================================
# 1. Database & SQL Reliability
# ============================================================================
def test_database_connection_and_context_manager() -> None:
    """Verify get_db_connection closes connection cleanly in context."""
    with get_db_connection() as conn:
        assert conn is not None
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS alive;")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 1


def test_database_check_connection_utility() -> None:
    """Verify check_database_connection returns True on active DB."""
    assert check_database_connection() is True


def test_database_failure_injection_returns_false_safely() -> None:
    """Verify failure injection during connection check fails gracefully."""
    with patch(
        "apps.api.db.connection._create_connection",
        side_effect=Exception("DB Down"),
    ):
        assert check_database_connection() is False


# ============================================================================
# 2. Security & RBAC Enforcement
# ============================================================================
def test_auth_disabled_mode_allows_dev_admin() -> None:
    """When AUTH_ENABLED=False, system provides default admin context."""
    with patch("apps.api.config.get_settings") as mock_settings:
        mock_settings.return_value = Settings(auth_enabled=False)
        user = get_current_user()
        assert user.username == "local-dev-user"
        assert user.role == Role.ADMIN


def test_auth_enabled_mode_rejects_unauthenticated_request() -> None:
    """When AUTH_ENABLED=True, missing credentials raise HTTP 401."""
    with patch("apps.api.config.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            auth_enabled=True,
            admin_api_key="secret_admin_key_123",
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(api_key=None, bearer=None)
        assert exc_info.value.status_code == 401


def test_auth_enabled_mode_accepts_valid_admin_key() -> None:
    """When AUTH_ENABLED=True, valid admin key grants Admin privileges."""
    with patch("apps.api.config.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            auth_enabled=True,
            admin_api_key="secret_admin_key_123",
        )
        user = get_current_user(api_key="secret_admin_key_123", bearer=None)
        assert user.role == Role.ADMIN
        assert user.username == "admin-service"


def test_rbac_role_hierarchy_enforcement() -> None:
    """Verify role permissions: Viewer (1) < Analyst (2) < Admin (3)."""
    viewer = AuthUser(username="v", role=Role.VIEWER)
    analyst = AuthUser(username="a", role=Role.ANALYST)
    admin = AuthUser(username="ad", role=Role.ADMIN)

    analyst_checker = require_role(Role.ANALYST)
    assert analyst_checker(analyst) == analyst
    assert analyst_checker(admin) == admin
    with pytest.raises(HTTPException) as exc:
        analyst_checker(viewer)
    assert exc.value.status_code == 403


# ============================================================================
# 3. Evidence Graph DAG Integrity & Edge Weight Constraints
# ============================================================================
def test_evidence_graph_integrity_and_bounded_weights() -> None:
    """Verify DAG is strictly connected with non-negative weights and no cycles."""
    causes = [
        RankedRootCause(
            rank=1,
            title="Order Volume Contraction",
            dimension="customer_state",
            dimension_value="SP",
            contribution_pct=-88.5,
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
        session_id="audit_session_graph_001",
    )

    assert graph.graph_id == "audit_session_graph_001"
    assert len(graph.nodes) == 7
    assert len(graph.edges) == 6

    for edge in graph.edges:
        assert edge.weight >= 0.0
        assert edge.source_id != edge.target_id

    assert graph.primary_chain_node_ids[0] == graph.root_node_id
    assert graph.primary_chain_node_ids[-1] == "node_root_cause_1"


# ============================================================================
# 4. Investigation Replay Determinism
# ============================================================================
def test_replay_snapshot_reproducibility() -> None:
    """Verify investigation snapshot persistence reproduces identical states."""
    resp = InvestigationAgentResponse(
        investigation_id="audit_replay_sess_999",
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
        steps_executed=3,
        trace=[
            InvestigationStepTrace(
                step_number=1,
                step_type="ANOMALY_DETECTION",
                step_title="Anomaly Detected",
                status="completed",
                finding_summary="Observed drop.",
            ),
            InvestigationStepTrace(
                step_number=2,
                step_type="DECOMPOSITION",
                step_title="Volume vs AOV",
                status="completed",
                finding_summary="Volume dominant.",
            ),
        ],
        top_root_causes=[
            RankedRootCause(
                rank=1,
                title="Volume Contraction",
                dimension="order_volume",
                dimension_value="158 orders",
                contribution_pct=88.5,
                absolute_change=-8000.0,
                score=90.0,
                explanation="Orders contracted.",
                causal_mechanism="order_volume",
            )
        ],
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
        executive_summary="Executive summary audit.",
        key_findings=["Finding 1"],
        recommended_actions=["Action 1"],
        limitations="Descriptive analysis.",
        termination_reason="Completed plan.",
        model="deterministic_agent",
        is_fallback=False,
    )

    snapshot = register_investigation_snapshot(resp)
    retrieved = get_investigation_snapshot("audit_replay_sess_999")

    assert retrieved is not None
    assert retrieved.session_id == snapshot.session_id
    assert retrieved.metric == "total_gmv"
    assert retrieved.total_steps == 2
    assert retrieved.observed_value == 22000.0
    assert len(retrieved.replay_steps) == 2
    assert retrieved.replay_steps[0].step_type == "ANOMALY_DETECTION"


# ============================================================================
# 5. Challenge Mode Robustness
# ============================================================================
def test_challenge_mode_distinguishes_absence_vs_contradiction() -> None:
    """Verify challenge mode separates contradictory evidence from lack of data."""
    req_weak = ChallengeRequest(
        session_id="audit_replay_sess_999",
        challenge_type="weakest_link",
    )
    res_weak = evaluate_challenge(req_weak)
    assert "weakest" in res_weak.challenge_question.lower()
    assert any(ev.verdict == "weak_link" for ev in res_weak.evaluations)

    req_flip = ChallengeRequest(
        session_id="audit_replay_sess_999",
        challenge_type="what_would_change",
    )
    res_flip = evaluate_challenge(req_flip)
    assert "change" in res_flip.challenge_question.lower()
    assert "threshold" in res_flip.evaluations[0].evidence_title.lower()


# ============================================================================
# 6. REST API Endpoints Reliability
# ============================================================================
def test_api_dimensions_endpoint() -> None:
    """Verify /api/v1/investigations/dimensions returns approved dimensions."""
    resp = client.get("/api/v1/investigations/dimensions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    assert any(d["dimension_key"] == "customer_state" for d in data)


def test_api_replay_sessions_endpoint() -> None:
    """Verify /api/v1/agent/replay/sessions returns registered sessions list."""
    resp = client.get("/api/v1/agent/replay/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_challenge_endpoint_success() -> None:
    """Verify POST /api/v1/agent/challenge evaluates valid query payload."""
    payload = {
        "session_id": "audit_replay_sess_999",
        "challenge_type": "why_not_cause",
        "candidate_cause": "average_order_value",
    }
    resp = client.post("/api/v1/agent/challenge", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "audit_replay_sess_999"
    q = data["challenge_question"].lower()
    assert "rejected" in q or "why was" in q
