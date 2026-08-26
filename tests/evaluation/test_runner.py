"""Unit tests for Benchmark Runner and Report Generator."""

import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
from evaluation.metrics.models import BenchmarkSummary, EvaluationResult
from evaluation.runners.run_benchmark import (
    generate_markdown_report,
    run_benchmark,
)


@pytest.fixture
def mock_agent_response() -> InvestigationAgentResponse:
    """Mock agent response for runner test."""
    return InvestigationAgentResponse(
        investigation_id="bench-test-01",
        anomaly_summary=AnomalySummary(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            baseline_start_date=date(2017, 11, 17),
            baseline_end_date=date(2017, 11, 23),
            observed_value=152654.0,
            baseline_value=31525.0,
            absolute_change=121129.0,
            percentage_change=384.2,
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
            )
        ],
        decomposition=VolumeValueDecomposition(
            observed_orders=1176,
            baseline_orders=206,
            observed_aov=129.8,
            baseline_aov=153.0,
            volume_effect=147944.0,
            aov_effect=-4709.0,
            interaction_effect=-22106.0,
            total_change=121129.0,
            volume_contribution_pct=85.0,
            aov_contribution_pct=-15.0,
            interaction_contribution_pct=0.0,
        ),
        top_root_causes=[
            RankedRootCause(
                rank=1,
                title="Order Volume Spike",
                dimension="order_volume",
                dimension_value="volume",
                contribution_pct=85.0,
                absolute_change=147944.0,
                score=95.0,
                explanation="Order volume explains majority of GMV shift",
            )
        ],
        supporting_evidence=[
            DimensionContributor(
                dimension="customer_state",
                dimension_value="SP",
                observed_value=38552.0,
                baseline_value=10000.0,
                absolute_change=28552.0,
                percentage_change=285.5,
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
        executive_summary="Order volume spike drove Black Friday revenue growth.",
        key_findings=["Order volume rose 469%"],
        recommended_actions=["Review regional inventory"],
        limitations="None",
        termination_reason="All scheduled branches evaluated.",
        model="gemini-1.5-flash",
        is_fallback=False,
    )


def test_markdown_report_generation() -> None:
    """Test generating formatted Markdown report."""
    res = EvaluationResult(
        scenario_id="SCN-006",
        scenario_name="Customer Acquisition Demand Surge",
        ground_truth_primary="order_volume_surge",
        top1_correct=True,
        top3_correct=True,
        reciprocal_rank=1.0,
        false_positive_rate=0.0,
        contribution_error=0.0,
        evidence_grounded=True,
        unsupported_claim_rate=0.0,
        hallucination_rate=0.0,
        investigation_steps=4,
        tool_calls=3,
        branches_explored=2,
        branches_pruned=1,
        execution_time_ms=180.5,
        stopping_reason="Completed",
    )

    summary = BenchmarkSummary(
        scenarios_evaluated=1,
        top1_accuracy=100.0,
        top3_accuracy=100.0,
        mrr=1.0,
        false_positive_rate=0.0,
        mean_contribution_error=0.0,
        evidence_grounding_rate=100.0,
        unsupported_claim_rate=0.0,
        hallucination_rate=0.0,
        avg_steps=4.0,
        avg_tool_calls=3.0,
        avg_execution_time_ms=180.5,
        results=[res],
    )

    md = generate_markdown_report(summary)
    assert "# RootCause AI Benchmark Report" in md
    assert "Top-1 Accuracy | 100.0%" in md
    assert "SCN-006" in md
    assert "180.5 ms" in md


@patch("evaluation.runners.run_benchmark.AutonomousInvestigationAgent")
def test_run_benchmark_mocked_execution(
    mock_agent_class: MagicMock,
    mock_agent_response: InvestigationAgentResponse,
    tmp_path: Path,
) -> None:
    """Test full benchmark runner execution with mocked agent response."""
    mock_agent_instance = MagicMock()
    mock_agent_instance.run_investigation.return_value = mock_agent_response
    mock_agent_class.return_value = mock_agent_instance

    json_out = str(tmp_path / "out.json")
    md_out = str(tmp_path / "out.md")

    mock_conn = MagicMock()

    summary = run_benchmark(
        scenario_id="SCN-006",
        output_json=json_out,
        output_md=md_out,
        conn=mock_conn,
    )

    assert summary.scenarios_evaluated == 1
    assert summary.top1_accuracy == 100.0
    assert Path(json_out).is_file()
    assert Path(md_out).is_file()

    with open(json_out, encoding="utf-8") as f:
        data = json.load(f)
        assert data["scenarios_evaluated"] == 1
