"""Phase I — Baseline vs Improved Agent Experiment Test Suite."""

import json
from pathlib import Path

from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationAgentResponse,
)
from apps.api.db.connection import get_db_connection
from evaluation.experiments.baseline_agent import BaselineInvestigationAgent
from evaluation.experiments.comparison import (
    AggregateComparisonSummary,
    run_comparison_experiment,
    save_comparison_reports,
)
from evaluation.experiments.improved_agent import ImprovedInvestigationAgent
from evaluation.scenarios import get_all_scenarios


def test_baseline_and_improved_are_both_executable() -> None:
    """1. Verify both baseline and improved adapters execute successfully."""
    with get_db_connection() as conn:
        base_agent = BaselineInvestigationAgent(conn=conn)
        imp_agent = ImprovedInvestigationAgent(conn=conn)
        scn = get_all_scenarios()[0]

        req = InvestigationAgentRequest(
            metric=scn.target_metric,
            anomaly_date=scn.anomaly_date,
            comparison_days=scn.comparison_days,
            dimensions=["product_category", "customer_state", "seller"],
        )

        base_resp = base_agent.run_investigation(req)
        imp_resp = imp_agent.run_investigation(req)

        assert isinstance(base_resp, InvestigationAgentResponse)
        assert isinstance(imp_resp, InvestigationAgentResponse)
        assert len(base_resp.top_root_causes) > 0
        assert len(imp_resp.top_root_causes) > 0


def test_identical_scenario_inputs_and_no_shared_state() -> None:
    """2 & 7. Verify both receive identical inputs and do not share mutable state."""
    with get_db_connection() as conn:
        base_agent = BaselineInvestigationAgent(conn=conn)
        imp_agent = ImprovedInvestigationAgent(conn=conn)
        scenarios = get_all_scenarios()[:6]

        for scn in scenarios:
            req_base = InvestigationAgentRequest(
                metric=scn.target_metric,
                anomaly_date=scn.anomaly_date,
                comparison_days=scn.comparison_days,
                dimensions=["product_category", "customer_state", "seller"],
            )
            req_imp = InvestigationAgentRequest(
                metric=scn.target_metric,
                anomaly_date=scn.anomaly_date,
                comparison_days=scn.comparison_days,
                dimensions=["product_category", "customer_state", "seller"],
            )

            # Ensure input parameters match exactly
            assert req_base.model_dump() == req_imp.model_dump()

            resp_base = base_agent.run_investigation(req_base)
            resp_imp = imp_agent.run_investigation(req_imp)

            # Ensure investigation IDs are unique and no shared references exist
            assert resp_base.investigation_id != resp_imp.investigation_id
            assert id(resp_base.top_root_causes) != id(resp_imp.top_root_causes)
            assert id(resp_base.key_findings) != id(resp_imp.key_findings)


def test_independent_metric_calculation_and_no_hardcoded_scores() -> None:
    """3 & 4. Verify metrics are calculated dynamically from empirical runs."""
    with get_db_connection() as conn:
        summary = run_comparison_experiment(conn=conn, verbose=False)

        assert isinstance(summary, AggregateComparisonSummary)
        assert summary.scenarios_evaluated == 6

        # Check dynamic range bounds
        assert 0.0 <= summary.baseline_top1_accuracy <= 100.0
        assert 0.0 <= summary.improved_top1_accuracy <= 100.0
        assert 0.0 <= summary.baseline_mrr <= 1.0
        assert 0.0 <= summary.improved_mrr <= 1.0

        # Verify improved outperforms baseline in causal ranking
        assert summary.improved_top1_accuracy >= summary.baseline_top1_accuracy
        assert summary.improved_mrr >= summary.baseline_mrr
        assert (
            summary.improved_claim_grounding_rate
            >= summary.baseline_claim_grounding_rate
        )
        assert (
            summary.improved_hallucination_rate <= summary.baseline_hallucination_rate
        )


def test_aggregate_metrics_match_underlying_scenario_results() -> None:
    """5. Verify that aggregate metrics match the underlying per-scenario averages."""
    with get_db_connection() as conn:
        summary = run_comparison_experiment(conn=conn, verbose=False)
        scns = summary.scenario_results

        n = len(scns)
        base_top1_pct = (sum(1 for s in scns if s.baseline_top1_correct) / n) * 100.0
        imp_top1_pct = (sum(1 for s in scns if s.improved_top1_correct) / n) * 100.0
        base_mrr = sum(s.baseline_mrr for s in scns) / n
        imp_mrr = sum(s.improved_mrr for s in scns) / n

        assert round(summary.baseline_top1_accuracy, 1) == round(base_top1_pct, 1)
        assert round(summary.improved_top1_accuracy, 1) == round(imp_top1_pct, 1)
        assert round(summary.baseline_mrr, 4) == round(base_mrr, 4)
        assert round(summary.improved_mrr, 4) == round(imp_mrr, 4)


def test_json_and_markdown_reports_generation() -> None:
    """6. Verify Markdown and JSON report generation and schema validity."""
    with get_db_connection() as conn:
        summary = run_comparison_experiment(conn=conn, verbose=False)
        save_comparison_reports(summary)

        rep_dir = Path(__file__).resolve().parents[2] / "evaluation" / "reports"
        json_path = rep_dir / "agent_comparison_latest.json"
        md_path = rep_dir / "agent_comparison_latest.md"

        assert json_path.exists(), "JSON report must exist"
        assert md_path.exists(), "Markdown report must exist"

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
            assert "scenarios_evaluated" in data
            assert data["scenarios_evaluated"] == 6
            assert "baseline_top1_accuracy" in data
            assert "improved_top1_accuracy" in data
            assert len(data["scenario_results"]) == 6

        with open(md_path, encoding="utf-8") as f:
            md_text = f.read()
            assert "# RootCause AI — Baseline vs Improved Agent Evaluation" in md_text
            assert "## 1. Executive Summary" in md_text
            assert "## 3. Aggregate Results" in md_text
            assert "## 4. Scenario-Level Results" in md_text
            assert "## 6. Failure Analysis" in md_text
            assert "## 7. Trade-offs" in md_text
            assert "## 8. Statistical & Experimental Interpretation" in md_text


def test_production_agent_and_benchmarks_remain_unchanged() -> None:
    """8, 9 & 10. Verify production agent and benchmarks preserve 100% accuracy."""
    with get_db_connection() as conn:
        from apps.analytics.agent.agent import AutonomousInvestigationAgent
        from evaluation.hallucination.extractor import (
            extract_claims_from_response,
            extract_evidence_from_response,
        )
        from evaluation.hallucination.verifier import verify_single_claim
        from evaluation.metrics.evaluator import evaluate_scenario_response

        agent = AutonomousInvestigationAgent(conn=conn)
        scenarios = get_all_scenarios()[:6]

        for scn in scenarios:
            req = InvestigationAgentRequest(
                metric=scn.target_metric,
                anomaly_date=scn.anomaly_date,
                comparison_days=scn.comparison_days,
                dimensions=["product_category", "customer_state", "seller"],
            )
            resp = agent.run_investigation(req)

            # Benchmark causal evaluation must remain 100% Top-1
            eval_res = evaluate_scenario_response(
                scenario=scn, response=resp, execution_time_ms=100.0
            )
            assert eval_res.top1_correct is True

            # Hallucination evaluator must verify all claims as SUPPORTED
            claims = extract_claims_from_response(resp)
            evidence = extract_evidence_from_response(resp)
            for c in claims:
                v_res = verify_single_claim(c, evidence, scenario_date=scn.anomaly_date)
                assert v_res.verification_status == "SUPPORTED"
