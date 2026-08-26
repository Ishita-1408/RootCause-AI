"""Unit tests for Evaluation Metrics, MRR, Accuracy, and Evidence Grounding."""

from datetime import date, datetime

from apps.analytics.agent.models import (
    InvestigationAgentResponse,
    InvestigationStepTrace,
    RankedRootCause,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)
from evaluation.metrics.evaluator import (
    aggregate_benchmark_results,
    evaluate_scenario_response,
)
from evaluation.metrics.models import EvaluationResult
from evaluation.scenarios.models import GroundTruthRootCause, GroundTruthScenario


def _create_mock_response(
    top_causes: list[RankedRootCause],
    decomposition: VolumeValueDecomposition | None = None,
    key_findings: list[str] | None = None,
) -> InvestigationAgentResponse:
    """Helper to build a typed mock response."""
    return InvestigationAgentResponse(
        investigation_id="test-inv-001",
        anomaly_summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            baseline_start_date=date(2017, 11, 17),
            baseline_end_date=date(2017, 11, 23),
            observed_value=150000.0,
            baseline_value=30000.0,
            absolute_change=120000.0,
            percentage_change=400.0,
            direction="increase",
        ),
        investigation_status="completed",
        steps_executed=4,
        trace=[
            InvestigationStepTrace(
                step_number=1,
                step_type="volume_aov_decomposition",
                step_title="Volume vs AOV Decomposition",
                status="completed",
                details={},
                executed_at=datetime(2026, 8, 26, 12, 0, 0),
            ),
            InvestigationStepTrace(
                step_number=2,
                step_type="customer_state_drilldown",
                step_title="Customer State Drilldown",
                status="completed",
                details={},
                executed_at=datetime(2026, 8, 26, 12, 0, 1),
            ),
            InvestigationStepTrace(
                step_number=3,
                step_type="seller_drilldown",
                step_title="Seller Drilldown",
                status="skipped",
                details={},
                executed_at=datetime(2026, 8, 26, 12, 0, 2),
                reason_if_skipped="Pruned: Low operational concentration",
            ),
        ],
        decomposition=decomposition
        or VolumeValueDecomposition(
            observed_orders=1176,
            baseline_orders=206,
            observed_aov=127.5,
            baseline_aov=145.6,
            volume_effect=140000.0,
            aov_effect=-20000.0,
            interaction_effect=0.0,
            total_change=120000.0,
            volume_contribution_pct=85.0,
            aov_contribution_pct=15.0,
            interaction_contribution_pct=0.0,
        ),
        top_root_causes=top_causes,
        supporting_evidence=[
            DimensionContributor(
                dimension="customer_state",
                dimension_value="SP",
                observed_value=50000.0,
                baseline_value=12000.0,
                absolute_change=38000.0,
                percentage_change=316.6,
                contribution_pct=32.0,
                direction="increase",
                rank=1,
            )
        ],
        operational_signals=OperationalIndicators(
            observed_late_delivery_rate=0.08,
            baseline_late_delivery_rate=0.05,
            late_delivery_rate_change=0.03,
            observed_avg_delivery_days=11.2,
            baseline_avg_delivery_days=10.5,
            avg_delivery_days_change=0.7,
            observed_cancellation_rate=0.01,
            baseline_cancellation_rate=0.01,
            cancellation_rate_change=0.0,
            observed_avg_review_score=4.15,
            baseline_avg_review_score=4.20,
            avg_review_score_change=-0.05,
        ),
        executive_summary="Order volume increase drove revenue growth.",
        key_findings=key_findings
        or ["Order volume grew 469%", "São Paulo SP was top regional driver"],
        recommended_actions=["Audit inventory capacity"],
        limitations="None",
        termination_reason="All scheduled branches evaluated.",
        model="gemini-1.5-flash",
        is_fallback=False,
    )


def test_top1_accuracy_and_mrr_rank1() -> None:
    """Test primary cause ranked at position 1 (Top-1, Top-3, MRR=1.0)."""
    scenario = GroundTruthScenario(
        scenario_id="SCN-T1",
        name="Test Scenario T1",
        description="Test",
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_spike",
            dimension="order_volume",
            expected_contribution_pct=85.0,
        ),
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
    )

    causes = [
        RankedRootCause(
            rank=1,
            title="Order Volume Surge",
            dimension="order_volume",
            dimension_value="volume",
            contribution_pct=85.0,
            absolute_change=140000.0,
            score=95.0,
            explanation="Order count increased",
        ),
        RankedRootCause(
            rank=2,
            title="State SP Volume",
            dimension="customer_state",
            dimension_value="SP",
            contribution_pct=32.0,
            absolute_change=38000.0,
            score=60.0,
            explanation="SP growth",
        ),
    ]

    resp = _create_mock_response(causes)
    result = evaluate_scenario_response(scenario, resp, execution_time_ms=120.0)

    assert result.top1_correct is True
    assert result.top3_correct is True
    assert result.reciprocal_rank == 1.0
    assert result.contribution_error == 0.0
    assert result.evidence_grounded is True
    assert result.unsupported_claim_rate == 0.0
    assert result.hallucination_rate == 0.0
    assert result.investigation_steps == 3
    assert result.tool_calls == 2
    assert result.branches_pruned == 1


def test_top3_accuracy_and_mrr_rank3() -> None:
    """Test primary cause ranked at position 3 (Top-1 False, Top-3 True, MRR=0.333)."""
    scenario = GroundTruthScenario(
        scenario_id="SCN-T2",
        name="Test Scenario T2",
        description="Test",
        primary_cause=GroundTruthRootCause(
            cause_id="delivery_delay",
            dimension="delivery",
        ),
        target_metric="late_delivery_rate_pct",
        anomaly_date=date(2017, 11, 24),
    )

    causes = [
        RankedRootCause(
            rank=1,
            title="Category Mix Shift",
            dimension="product_category",
            dimension_value="cama_mesa_banho",
            contribution_pct=40.0,
            absolute_change=5000.0,
            score=70.0,
            explanation="Category shift",
        ),
        RankedRootCause(
            rank=2,
            title="Seller Delays",
            dimension="seller",
            dimension_value="seller_123",
            contribution_pct=25.0,
            absolute_change=3000.0,
            score=50.0,
            explanation="Seller delays",
        ),
        RankedRootCause(
            rank=3,
            title="Delivery Transit SLA Delay",
            dimension="delivery",
            dimension_value="carrier_delay",
            contribution_pct=20.0,
            absolute_change=0.04,
            score=45.0,
            explanation="Late delivery increase",
        ),
    ]

    resp = _create_mock_response(causes)
    result = evaluate_scenario_response(scenario, resp, execution_time_ms=150.0)

    assert result.top1_correct is False
    assert result.top3_correct is True
    assert round(result.reciprocal_rank, 3) == 0.333
    assert result.failure_explanation is not None


def test_correct_cause_absent() -> None:
    """Test primary cause completely absent (Top-1 False, Top-3 False, MRR=0.0)."""
    scenario = GroundTruthScenario(
        scenario_id="SCN-T3",
        name="Test Scenario T3",
        description="Test",
        primary_cause=GroundTruthRootCause(
            cause_id="pricing_elasticity",
            dimension="average_order_value",
        ),
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
    )

    causes = [
        RankedRootCause(
            rank=1,
            title="Order Volume Growth",
            dimension="order_volume",
            dimension_value="volume",
            contribution_pct=90.0,
            absolute_change=120000.0,
            score=90.0,
            explanation="Orders surged",
        )
    ]

    resp = _create_mock_response(causes)
    result = evaluate_scenario_response(scenario, resp, execution_time_ms=100.0)

    assert result.top1_correct is False
    assert result.top3_correct is False
    assert result.reciprocal_rank == 0.0


def test_empty_predictions_handling() -> None:
    """Test edge case with empty predictions array."""
    scenario = GroundTruthScenario(
        scenario_id="SCN-T4",
        name="Test Scenario T4",
        description="Test",
        primary_cause=GroundTruthRootCause(
            cause_id="order_volume_spike",
            dimension="order_volume",
        ),
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
    )

    resp = _create_mock_response([])
    result = evaluate_scenario_response(scenario, resp, execution_time_ms=50.0)

    assert result.top1_correct is False
    assert result.top3_correct is False
    assert result.reciprocal_rank == 0.0
    assert result.false_positive_rate == 0.0


def test_benchmark_aggregation() -> None:
    """Test aggregate_benchmark_results calculation."""
    r1 = EvaluationResult(
        scenario_id="SCN-001",
        scenario_name="S1",
        ground_truth_primary="c1",
        top1_correct=True,
        top3_correct=True,
        reciprocal_rank=1.0,
        false_positive_rate=0.0,
        contribution_error=5.0,
        evidence_grounded=True,
        unsupported_claim_rate=0.0,
        hallucination_rate=0.0,
        investigation_steps=4,
        tool_calls=3,
        execution_time_ms=200.0,
    )
    r2 = EvaluationResult(
        scenario_id="SCN-002",
        scenario_name="S2",
        ground_truth_primary="c2",
        top1_correct=False,
        top3_correct=True,
        reciprocal_rank=0.5,
        false_positive_rate=0.33,
        contribution_error=15.0,
        evidence_grounded=True,
        unsupported_claim_rate=0.0,
        hallucination_rate=0.0,
        investigation_steps=6,
        tool_calls=5,
        execution_time_ms=400.0,
    )

    summary = aggregate_benchmark_results([r1, r2])

    assert summary.scenarios_evaluated == 2
    assert summary.top1_accuracy == 50.0
    assert summary.top3_accuracy == 100.0
    assert summary.mrr == 0.75
    assert summary.mean_contribution_error == 10.0
    assert summary.evidence_grounding_rate == 100.0
    assert summary.avg_steps == 5.0
    assert summary.avg_tool_calls == 4.0
    assert summary.avg_execution_time_ms == 300.0


# ---------------------------------------------------------------------------
# Structured Causal Evaluator v2 Unit Tests (Requirement 5)
# ---------------------------------------------------------------------------


def test_exact_mechanism_match() -> None:
    """Verify exact structured causal mechanism matching across all primary types."""
    from evaluation.metrics.evaluator import _matches_cause

    target_vol = GroundTruthRootCause(
        cause_id="order_volume_drop",
        dimension="order_volume",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
    )
    pred_vol = RankedRootCause(
        rank=1,
        title="Order Volume Contraction",
        dimension="order_volume",
        dimension_value="volume",
        contribution_pct=80.0,
        absolute_change=-50000.0,
        score=90.0,
        explanation="Orders dropped",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
    )
    assert _matches_cause(pred_vol, target_vol) is True

    target_aov = GroundTruthRootCause(
        cause_id="average_order_value_expansion",
        dimension="average_order_value",
        causal_category="macro_driver",
        causal_mechanism="average_order_value",
    )
    pred_aov = RankedRootCause(
        rank=1,
        title="Average Order Value Expansion",
        dimension="average_order_value",
        dimension_value="aov",
        contribution_pct=60.0,
        absolute_change=30000.0,
        score=85.0,
        explanation="Basket size expanded",
        causal_category="macro_driver",
        causal_mechanism="average_order_value",
    )
    assert _matches_cause(pred_aov, target_aov) is True

    target_del = GroundTruthRootCause(
        cause_id="carrier_sla_degradation",
        dimension="delivery",
        causal_category="operational_mechanism",
        causal_mechanism="delivery",
    )
    pred_del = RankedRootCause(
        rank=1,
        title="Carrier SLA Degradation",
        dimension="delivery",
        dimension_value="carrier_transit_delay",
        contribution_pct=100.0,
        absolute_change=1000.0,
        score=95.0,
        explanation="Transit delays",
        causal_category="operational_mechanism",
        causal_mechanism="delivery",
    )
    assert _matches_cause(pred_del, target_del) is True


def test_wording_differences_with_same_mechanism() -> None:
    """Verify wording variations match if structured mechanism is identical."""
    from evaluation.metrics.evaluator import _matches_cause

    target = GroundTruthRootCause(
        cause_id="order_volume_surge",
        dimension="order_volume",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
    )

    # Various natural language phrasings
    phrasings = [
        "More orders",
        "Order volume increased",
        "Demand volume surge",
        "Massive transaction surge on Black Friday",
        "Headline gross transaction volume surge",
    ]

    for title in phrasings:
        pred = RankedRootCause(
            rank=1,
            title=title,
            dimension="order_volume",
            dimension_value="volume",
            contribution_pct=90.0,
            absolute_change=150000.0,
            score=95.0,
            explanation=f"Explanation: {title}",
            causal_category="macro_driver",
            causal_mechanism="order_volume",
        )
        assert _matches_cause(pred, target) is True, (
            f"Failed to match phrasing '{title}'"
        )


def test_wrong_mechanism() -> None:
    """Verify that a prediction with an incorrect causal mechanism is rejected."""
    from evaluation.metrics.evaluator import _matches_cause

    target_vol = GroundTruthRootCause(
        cause_id="order_volume_drop",
        dimension="order_volume",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
    )

    pred_aov = RankedRootCause(
        rank=1,
        title="Average Order Value Shift",
        dimension="average_order_value",
        dimension_value="aov",
        contribution_pct=50.0,
        absolute_change=-20000.0,
        score=80.0,
        explanation="AOV dropped",
        causal_category="macro_driver",
        causal_mechanism="average_order_value",
    )
    assert _matches_cause(pred_aov, target_vol) is False

    pred_del = RankedRootCause(
        rank=1,
        title="Delivery Bottleneck",
        dimension="delivery",
        dimension_value="late_delivery",
        contribution_pct=100.0,
        absolute_change=500.0,
        score=75.0,
        explanation="Late deliveries",
        causal_category="operational_mechanism",
        causal_mechanism="delivery",
    )
    assert _matches_cause(pred_del, target_vol) is False


def test_correct_mechanism_wrong_segment() -> None:
    """Verify mechanism matches even if segment differs from secondary targets."""
    from evaluation.metrics.evaluator import _matches_cause

    target = GroundTruthRootCause(
        cause_id="order_volume_surge",
        dimension="order_volume",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
        affected_dimension="customer_state",
        affected_value="SP",
    )

    # Primary causal mechanism prediction with a different concentrated slice
    pred = RankedRootCause(
        rank=1,
        title="Order Volume Surge",
        dimension="order_volume",
        dimension_value="volume",
        contribution_pct=85.0,
        absolute_change=120000.0,
        score=95.0,
        explanation="Volume surge concentrated in RJ",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
        affected_dimension="customer_state",
        affected_value="RJ",
    )
    # The primary causal mechanism matches correctly
    assert _matches_cause(pred, target) is True


def test_segment_only_prediction_does_not_match_mechanism() -> None:
    """Verify segment concentration NEVER matches a causal mechanism."""
    from evaluation.metrics.evaluator import _matches_cause

    target_mech = GroundTruthRootCause(
        cause_id="order_volume_drop",
        dimension="order_volume",
        causal_category="macro_driver",
        causal_mechanism="order_volume",
    )

    # Segment-only prediction without causal mechanism
    pred_segment = RankedRootCause(
        rank=1,
        title="Customer State: SP",
        dimension="customer_state",
        dimension_value="SP",
        contribution_pct=40.0,
        absolute_change=-35000.0,
        score=70.0,
        explanation="São Paulo state drop",
        causal_category="segment_concentration",
        causal_mechanism=None,
        affected_dimension="customer_state",
        affected_value="SP",
    )

    assert _matches_cause(pred_segment, target_mech) is False

    # Another segment
    pred_category = RankedRootCause(
        rank=1,
        title="Product Category: cama_mesa_banho",
        dimension="product_category",
        dimension_value="cama_mesa_banho",
        contribution_pct=30.0,
        absolute_change=-25000.0,
        score=65.0,
        explanation="Category decline",
        causal_category="segment_concentration",
        causal_mechanism=None,
        affected_dimension="product_category",
        affected_value="cama_mesa_banho",
    )
    assert _matches_cause(pred_category, target_mech) is False


def test_missing_mechanism_handling() -> None:
    """Verify handling of predictions with missing or unknown mechanism."""
    from evaluation.metrics.evaluator import _matches_cause

    target = GroundTruthRootCause(
        cause_id="delivery_delay",
        dimension="delivery",
        causal_category="operational_mechanism",
        causal_mechanism="delivery",
    )

    pred_empty = RankedRootCause(
        rank=1,
        title="Unknown Cause",
        dimension="",
        dimension_value="",
        contribution_pct=0.0,
        absolute_change=0.0,
        score=0.0,
        explanation="No data",
        causal_category="segment_concentration",
        causal_mechanism=None,
    )
    assert _matches_cause(pred_empty, target) is False


def test_multiple_candidate_causes_ranking() -> None:
    """Verify evaluation with multiple causes ranked (correct cause at rank 2)."""
    scenario = GroundTruthScenario(
        scenario_id="SCN-MULTI",
        name="Multi Candidate Test",
        description="Testing ranking order",
        primary_cause=GroundTruthRootCause(
            cause_id="average_order_value_expansion",
            dimension="average_order_value",
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
        ),
        target_metric="total_gmv",
        anomaly_date=date(2017, 11, 27),
    )

    causes = [
        # Rank 1: Segment concentration (wrong for primary mechanism)
        RankedRootCause(
            rank=1,
            title="Customer State: SP",
            dimension="customer_state",
            dimension_value="SP",
            contribution_pct=50.0,
            absolute_change=25000.0,
            score=90.0,
            explanation="SP growth",
            causal_category="segment_concentration",
            causal_mechanism=None,
        ),
        # Rank 2: Correct AOV mechanism
        RankedRootCause(
            rank=2,
            title="Average Order Value Expansion",
            dimension="average_order_value",
            dimension_value="aov",
            contribution_pct=60.0,
            absolute_change=30000.0,
            score=85.0,
            explanation="Basket size expanded",
            causal_category="macro_driver",
            causal_mechanism="average_order_value",
        ),
    ]

    resp = _create_mock_response(causes)
    result = evaluate_scenario_response(scenario, resp, execution_time_ms=100.0)

    assert result.top1_correct is False
    assert result.top3_correct is True
    assert result.reciprocal_rank == 0.5


def test_causal_mechanism_aliases() -> None:
    """Verify that standard mechanism aliases resolve to canonical identifiers."""
    from evaluation.metrics.evaluator import canonicalize_mechanism

    # Volume aliases
    assert canonicalize_mechanism("order_volume") == "order_volume"
    assert canonicalize_mechanism("volume") == "order_volume"
    assert canonicalize_mechanism("orders_count") == "order_volume"
    assert canonicalize_mechanism("order_volume_drop") == "order_volume"
    assert canonicalize_mechanism("order_volume_surge") == "order_volume"

    # AOV aliases
    assert canonicalize_mechanism("average_order_value") == "average_order_value"
    assert canonicalize_mechanism("aov") == "average_order_value"
    assert canonicalize_mechanism("basket_size") == "average_order_value"
    assert canonicalize_mechanism("pricing") == "average_order_value"
    assert (
        canonicalize_mechanism("average_order_value_expansion") == "average_order_value"
    )

    # Delivery aliases
    assert canonicalize_mechanism("delivery") == "delivery"
    assert canonicalize_mechanism("carrier_sla") == "delivery"
    assert canonicalize_mechanism("carrier_transit_delay") == "delivery"
    assert canonicalize_mechanism("logistics_fulfillment_bottleneck") == "delivery"
    assert canonicalize_mechanism("late_delivery_rate_pct") == "delivery"
