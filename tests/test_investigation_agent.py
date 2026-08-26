"""Unit and integration tests for Phase 8 Autonomous Investigation Agent."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.analytics.agent import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
    InvestigationState,
    calculate_root_cause_score,
    generate_initial_plan,
    rank_evidence,
    run_autonomous_investigation,
    should_skip_branch,
    should_terminate,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    VolumeValueDecomposition,
)
from apps.api.main import app

client = TestClient(app)


# 1. Investigation Planning Tests
def test_investigation_planning_initial_queue() -> None:
    """Test deterministic generation of initial investigation queue."""
    req_gmv = InvestigationAgentRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        dimensions=["customer_state", "product_category", "seller"],
    )
    plan_gmv = generate_initial_plan(req_gmv)
    assert plan_gmv[0] == "volume_aov_decomposition"
    assert "customer_state_drilldown" in plan_gmv
    assert "product_category_drilldown" in plan_gmv
    assert "seller_drilldown" in plan_gmv

    req_orders = InvestigationAgentRequest(
        metric="orders_count",
        anomaly_date=date(2017, 11, 24),
        dimensions=["customer_state"],
    )
    plan_orders = generate_initial_plan(req_orders)
    # orders_count does not need volume/aov decomposition
    assert "volume_aov_decomposition" not in plan_orders
    assert plan_orders[0] == "customer_state_drilldown"


# 2. Evidence Ranking and Mathematical Scoring Tests
def test_evidence_ranking_scoring_formula() -> None:
    """Test deterministic scoring formula behavior."""
    # Higher contribution % with significant magnitude should yield higher score
    score_high = calculate_root_cause_score(
        contribution_pct=31.8,
        absolute_change=38551.68,
        dimension="customer_state",
    )
    score_low = calculate_root_cause_score(
        contribution_pct=8.2,
        absolute_change=9950.0,
        dimension="product_category",
    )

    assert score_high > score_low
    assert score_high > 0.0

    # Negative contribution percentages should use absolute magnitude for ranking
    score_neg = calculate_root_cause_score(
        contribution_pct=-15.0,
        absolute_change=-18000.0,
        dimension="product_category",
    )
    assert score_neg > 0.0


def test_rank_evidence_macro_and_micro_mix() -> None:
    """Test ranking macro Volume/AOV drivers alongside granular slices."""
    decomp = VolumeValueDecomposition(
        observed_orders=1176.0,
        baseline_orders=207.0,
        observed_aov=129.81,
        baseline_aov=152.61,
        volume_effect=147944.71,
        aov_effect=-4709.80,
        interaction_effect=-22103.00,
        total_change=121128.81,
        volume_contribution_pct=122.14,
        aov_contribution_pct=-3.89,
        interaction_contribution_pct=-18.25,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=50000.0,
            baseline_value=11448.32,
            absolute_change=38551.68,
            percentage_change=336.75,
            contribution_pct=31.83,
            direction="increase",
            rank=1,
        ),
        DimensionContributor(
            dimension="product_category",
            dimension_value="cama_mesa_banho",
            observed_value=20000.0,
            baseline_value=4000.0,
            absolute_change=16000.0,
            percentage_change=400.0,
            contribution_pct=13.21,
            direction="increase",
            rank=2,
        ),
    ]

    ranked = rank_evidence(
        contributors=contributors, decomposition=decomp, max_causes=3
    )
    assert len(ranked) == 3
    # Volume shift should rank at the top
    assert ranked[0].dimension == "order_volume"
    assert ranked[0].rank == 1
    assert ranked[1].dimension_value == "SP"
    assert ranked[1].rank == 2


# 3. Stopping Policy Tests
def test_stopping_policy_max_steps() -> None:
    """Test termination when max step limit is reached."""
    state = InvestigationState(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        current_step=6,
        max_steps=6,
        pending_steps=["seller_drilldown"],
    )
    should_stop, reason = should_terminate(state)
    assert should_stop is True
    assert "Investigation limit" in str(reason)


def test_stopping_policy_empty_queue() -> None:
    """Test normal completion when pending queue is empty."""
    state = InvestigationState(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        current_step=4,
        max_steps=6,
        pending_steps=[],
    )
    should_stop, reason = should_terminate(state)
    assert should_stop is True
    assert "All scheduled branches" in str(reason)


def test_branch_skip_policy_low_operational_signal() -> None:
    """Test skipping operational branch when late delivery rate did not change."""
    op_indicators = OperationalIndicators(
        observed_late_delivery_rate=14.5,
        baseline_late_delivery_rate=14.2,
        late_delivery_rate_change=0.3,  # < 1.0% threshold
        observed_avg_delivery_days=12.2,
        baseline_avg_delivery_days=12.0,
        avg_delivery_days_change=0.2,  # < 1.0d threshold
        observed_cancellation_rate=0.2,
        baseline_cancellation_rate=0.2,
        cancellation_rate_change=0.0,
        observed_avg_review_score=4.0,
        baseline_avg_review_score=4.0,
        avg_review_score_change=0.0,
    )
    evidence = {"operational_indicators": op_indicators}

    skip, reason = should_skip_branch(
        "operational_signals_evaluation", evidence=evidence
    )
    assert skip is True
    assert "Operational signals stable" in str(reason)


# 4. Request Validation & State Serialization Tests
def test_agent_request_validation() -> None:
    """Test validation errors for unapproved metric or empty dimensions."""
    with pytest.raises(ValueError):
        InvestigationAgentRequest(
            metric="unapproved_kpi",  # type: ignore[arg-type]
            anomaly_date=date(2017, 11, 24),
        )

    with pytest.raises(ValueError):
        InvestigationAgentRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            dimensions=[],  # Empty dimensions
        )


def test_state_serialization_to_json() -> None:
    """Test serialization of InvestigationState."""
    state = InvestigationState(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
    )
    json_str = state.model_dump_json()
    assert "inv_" in json_str
    assert "total_gmv" in json_str


# 5. Agent Orchestration Mocked Test
@patch("apps.analytics.agent.executor.investigate_root_cause")
def test_autonomous_investigation_orchestration_mocked(
    mock_rc: MagicMock,
) -> None:
    """Test full agent orchestration cycle with mocked deterministic engine."""
    mock_rc.return_value = RootCauseInvestigationResponse(
        request=RootCauseInvestigationRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
        ),
        summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            baseline_start_date=date(2017, 11, 17),
            baseline_end_date=date(2017, 11, 23),
            observed_value=152653.74,
            baseline_value=31524.93,
            absolute_change=121128.81,
            percentage_change=384.2,
            direction="increase",
        ),
        decomposition=VolumeValueDecomposition(
            observed_orders=1176.0,
            baseline_orders=207.0,
            observed_aov=129.81,
            baseline_aov=152.61,
            volume_effect=147944.71,
            aov_effect=-4709.80,
            interaction_effect=-22103.00,
            total_change=121128.81,
            volume_contribution_pct=122.14,
            aov_contribution_pct=-3.89,
            interaction_contribution_pct=-18.25,
        ),
        ranked_contributors=[
            DimensionContributor(
                dimension="customer_state",
                dimension_value="SP",
                observed_value=50000.0,
                baseline_value=11448.32,
                absolute_change=38551.68,
                percentage_change=336.75,
                contribution_pct=31.83,
                direction="increase",
                rank=1,
            )
        ],
        operational_indicators=OperationalIndicators(
            observed_late_delivery_rate=20.0,
            baseline_late_delivery_rate=14.2,
            late_delivery_rate_change=5.8,
            observed_avg_delivery_days=17.2,
            baseline_avg_delivery_days=12.5,
            avg_delivery_days_change=4.7,
            observed_cancellation_rate=0.4,
            baseline_cancellation_rate=0.2,
            cancellation_rate_change=0.2,
            observed_avg_review_score=3.73,
            baseline_avg_review_score=3.94,
            avg_review_score_change=-0.21,
        ),
        explanation="TOTAL_GMV shifted +384.2% on 2017-11-24.",
        limitations="Non-causal.",
    )

    mock_conn = MagicMock()
    req = InvestigationAgentRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        dimensions=["customer_state", "product_category"],
        max_investigation_steps=5,
    )

    resp = run_autonomous_investigation(conn=mock_conn, request=req)

    assert isinstance(resp, InvestigationAgentResponse)
    assert resp.steps_executed > 0
    assert len(resp.trace) > 0
    assert resp.top_root_causes[0].dimension in (
        "order_volume",
        "customer_state",
    )
    assert resp.investigation_status in ("completed", "max_steps_reached")


# 6. FastAPI Router Tests
def test_agent_health_endpoint() -> None:
    """Test GET /api/v1/agent/health."""
    resp = client.get("/api/v1/agent/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "autonomous_investigation_agent"


@patch("apps.api.routers.agent.get_db_connection")
@patch("apps.api.routers.agent.run_autonomous_investigation")
def test_agent_investigate_endpoint_success(
    mock_agent: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/agent/investigate."""
    mock_agent.return_value = InvestigationAgentResponse(
        investigation_id="inv_test123",
        anomaly_summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            baseline_start_date=date(2017, 11, 17),
            baseline_end_date=date(2017, 11, 23),
            observed_value=152653.74,
            baseline_value=31524.93,
            absolute_change=121128.81,
            percentage_change=384.2,
            direction="increase",
        ),
        investigation_status="completed",
        steps_executed=4,
        trace=[],
        decomposition=None,
        top_root_causes=[],
        supporting_evidence=[],
        operational_signals=OperationalIndicators(
            observed_late_delivery_rate=20.0,
            baseline_late_delivery_rate=14.2,
            late_delivery_rate_change=5.8,
            observed_avg_delivery_days=17.2,
            baseline_avg_delivery_days=12.5,
            avg_delivery_days_change=4.7,
            observed_cancellation_rate=0.4,
            baseline_cancellation_rate=0.2,
            cancellation_rate_change=0.2,
            observed_avg_review_score=3.73,
            baseline_avg_review_score=3.94,
            avg_review_score_change=-0.21,
        ),
        executive_summary="GMV increased +384.2% on Black Friday.",
        key_findings=["Volume driver +469.3%."],
        recommended_actions=["Align carrier dispatch."],
        limitations="Non-causal.",
        termination_reason="Completed.",
        model="gpt-4o-mini",
        is_fallback=False,
    )

    resp = client.post(
        "/api/v1/agent/investigate",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2017-11-24",
            "comparison_days": 7,
            "dimensions": ["customer_state", "product_category"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["investigation_id"] == "inv_test123"
    assert data["anomaly_summary"]["percentage_change"] == 384.2


# 6. Phase C Causal Reasoning & Separation Tests
def test_phase_c_delivery_causal_mechanism_outranks_sp_slice() -> None:
    """Test SCN-001 regression: delivery mechanism outranks SP geographic slice."""
    summary = AnomalySummary(
        metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 3, 15),
        baseline_start_date=date(2018, 3, 8),
        baseline_end_date=date(2018, 3, 14),
        observed_value=0.18,
        baseline_value=0.08,
        absolute_change=0.10,
        percentage_change=125.0,
        direction="increase",
    )
    op = OperationalIndicators(
        observed_late_delivery_rate=0.18,
        baseline_late_delivery_rate=0.08,
        late_delivery_rate_change=0.10,
        observed_avg_delivery_days=18.5,
        baseline_avg_delivery_days=11.2,
        avg_delivery_days_change=7.3,
        observed_cancellation_rate=0.02,
        baseline_cancellation_rate=0.01,
        cancellation_rate_change=0.01,
        observed_avg_review_score=3.5,
        baseline_avg_review_score=4.2,
        avg_review_score_change=-0.7,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=0.22,
            baseline_value=0.09,
            absolute_change=0.13,
            percentage_change=144.4,
            contribution_pct=130.0,
            direction="increase",
            rank=1,
        ),
        DimensionContributor(
            dimension="customer_state",
            dimension_value="RJ",
            observed_value=0.19,
            baseline_value=0.10,
            absolute_change=0.09,
            percentage_change=90.0,
            contribution_pct=90.0,
            direction="increase",
            rank=2,
        ),
    ]

    ranked = rank_evidence(
        contributors=contributors,
        summary=summary,
        operational_signals=op,
        max_causes=3,
    )

    # 1. Macro Delivery Causal Mechanism MUST rank #1
    assert ranked[0].dimension == "delivery"
    assert ranked[0].causal_category == "operational_mechanism"
    assert ranked[0].causal_mechanism == "delivery"
    assert ranked[0].affected_dimension == "customer_state"
    assert ranked[0].affected_value == "SP"
    assert len(ranked[0].evidence_chain) >= 3

    # 2. Geographic concentration slice SP ranks secondary
    assert ranked[1].dimension == "customer_state"
    assert ranked[1].dimension_value == "SP"
    assert ranked[1].causal_category == "segment_concentration"


def test_phase_c_carrier_sla_outranks_mg_slice() -> None:
    """Test SCN-004 regression: carrier SLA outranks MG slice."""
    summary = AnomalySummary(
        metric="late_delivery_rate_pct",
        anomaly_date=date(2018, 5, 20),
        baseline_start_date=date(2018, 5, 13),
        baseline_end_date=date(2018, 5, 19),
        observed_value=0.25,
        baseline_value=0.10,
        absolute_change=0.15,
        percentage_change=150.0,
        direction="increase",
    )
    op = OperationalIndicators(
        observed_late_delivery_rate=0.25,
        baseline_late_delivery_rate=0.10,
        late_delivery_rate_change=0.15,
        observed_avg_delivery_days=21.0,
        baseline_avg_delivery_days=13.0,
        avg_delivery_days_change=8.0,
        observed_cancellation_rate=0.03,
        baseline_cancellation_rate=0.01,
        cancellation_rate_change=0.02,
        observed_avg_review_score=3.2,
        baseline_avg_review_score=4.1,
        avg_review_score_change=-0.9,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="MG",
            observed_value=0.30,
            baseline_value=0.11,
            absolute_change=0.19,
            percentage_change=172.7,
            contribution_pct=126.7,
            direction="increase",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        summary=summary,
        operational_signals=op,
        max_causes=3,
    )

    assert ranked[0].dimension == "delivery"
    assert ranked[0].causal_category == "operational_mechanism"
    assert ranked[0].affected_value == "MG"


def test_phase_c_evidence_chain_and_grounding_invariants() -> None:
    """Test evidence chain population and zero hallucination invariants."""
    decomp = VolumeValueDecomposition(
        observed_orders=1000.0,
        baseline_orders=500.0,
        observed_aov=100.0,
        baseline_aov=100.0,
        volume_effect=50000.0,
        aov_effect=0.0,
        interaction_effect=0.0,
        total_change=50000.0,
        volume_contribution_pct=100.0,
        aov_contribution_pct=0.0,
        interaction_contribution_pct=0.0,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=40000.0,
            baseline_value=15000.0,
            absolute_change=25000.0,
            percentage_change=166.7,
            contribution_pct=50.0,
            direction="increase",
            rank=1,
        )
    ]

    ranked = rank_evidence(
        contributors=contributors,
        decomposition=decomp,
        max_causes=2,
    )

    for cause in ranked:
        assert len(cause.evidence_chain) > 0
        assert cause.evidence_strength in ["high", "medium", "low", "insufficient"]
        assert 0.0 <= cause.confidence <= 1.0
