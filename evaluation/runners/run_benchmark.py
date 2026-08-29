"""Benchmark Execution Runner and CLI for RootCause AI (Phase B)."""

import argparse
import logging
import time
from pathlib import Path
from typing import Any

from apps.analytics.agent import (
    AutonomousInvestigationAgent,
    InvestigationAgentRequest,
)
from apps.api.db.connection import get_db_connection
from evaluation.metrics.evaluator import (
    aggregate_benchmark_results,
    evaluate_scenario_response,
)
from evaluation.metrics.models import BenchmarkSummary, EvaluationResult
from evaluation.scenarios.models import GroundTruthScenario
from evaluation.scenarios.registry import (
    get_all_scenarios,
    get_scenario,
)

logger = logging.getLogger("evaluation.benchmark")
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def generate_markdown_report(summary: BenchmarkSummary) -> str:
    """Format benchmark summary into an executive Markdown report."""
    err_val = (
        f"{summary.mean_contribution_error:.1f}%"
        if summary.mean_contribution_error is not None
        else "N/A"
    )
    easy_acc = (
        f"{summary.easy_top1_accuracy:.1f}%"
        if summary.easy_top1_accuracy is not None
        else "N/A"
    )
    easy_mrr_str = f"{summary.easy_mrr:.4f}" if summary.easy_mrr is not None else "N/A"
    med_acc = (
        f"{summary.medium_top1_accuracy:.1f}%"
        if summary.medium_top1_accuracy is not None
        else "N/A"
    )
    med_mrr_str = (
        f"{summary.medium_mrr:.4f}" if summary.medium_mrr is not None else "N/A"
    )
    hard_acc = (
        f"{summary.hard_top1_accuracy:.1f}%"
        if summary.hard_top1_accuracy is not None
        else "N/A"
    )
    hard_mrr_str = f"{summary.hard_mrr:.4f}" if summary.hard_mrr is not None else "N/A"

    lines = [
        "# RootCause AI Benchmark Report (Structured Causal Evaluator v2)",
        "",
        "## Overall Results",
        "",
        "| Metric | Score |",
        "|---|---:|",
        f"| Scenarios Evaluated | {summary.scenarios_evaluated} |",
        f"| Top-1 Accuracy | {summary.top1_accuracy:.1f}% |",
        f"| Top-3 Accuracy | {summary.top3_accuracy:.1f}% |",
        f"| Mean Reciprocal Rank (MRR) | {summary.mrr:.4f} |",
        f"| False Positive Rate | {summary.false_positive_rate:.3f} |",
        f"| Mean Contribution Error | {err_val} |",
        f"| Evidence Grounding Rate | {summary.evidence_grounding_rate:.1f}% |",
        f"| Unsupported Claim Rate | {summary.unsupported_claim_rate:.3f} |",
        f"| Hallucination Rate | {summary.hallucination_rate:.3f} |",
        f"| Avg Investigation Steps | {summary.avg_steps:.1f} |",
        f"| Avg Analytical Tool Calls | {summary.avg_tool_calls:.1f} |",
        f"| Avg Execution Time | {summary.avg_execution_time_ms:.1f} ms |",
        "",
        "## Difficulty Stratification",
        "",
        "| Tier | Scenarios | Top-1 Accuracy | MRR |",
        "|---|---:|---:|---:|",
        (
            f"| **Easy** (Clear Single Driver) | {summary.easy_count}"
            f" | {easy_acc} | {easy_mrr_str} |"
        ),
        (
            f"| **Medium** (Multi-Factor Drivers) | {summary.medium_count}"
            f" | {med_acc} | {med_mrr_str} |"
        ),
        (
            f"| **Hard** (Competing / Distractors / Noise) | {summary.hard_count}"
            f" | {hard_acc} | {hard_mrr_str} |"
        ),
        "",
        "## Scenario Results",
        "",
        (
            "| Scenario | Difficulty | Ground Truth"
            " | Top-1 | Top-3 | MRR | Error | Grounded |"
        ),
        "|---|:---:|---|:---:|:---:|:---:|:---:|:---:|",
    ]

    for r in summary.results:
        top1_sym = "✓" if r.top1_correct else "✗"
        top3_sym = "✓" if r.top3_correct else "✗"
        ground_sym = "✓" if r.evidence_grounded else "✗"
        err_str = (
            f"{r.contribution_error:.1f}%"
            if r.contribution_error is not None
            else "N/A"
        )
        row = (
            f"| **{r.scenario_id}** | `{r.difficulty}` | `{r.ground_truth_primary}` | "
            f"{top1_sym} | {top3_sym} | {r.reciprocal_rank:.3f} | "
            f"{err_str} | {ground_sym} |"
        )
        lines.append(row)

    lines.extend(
        [
            "",
            "## Investigation Efficiency",
            "",
            "| Scenario | Steps | Tools | Branches | Pruned | Execution Time |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for r in summary.results:
        row = (
            f"| **{r.scenario_id}** | {r.investigation_steps} | "
            f"{r.tool_calls} | {r.branches_explored} | "
            f"{r.branches_pruned} | {r.execution_time_ms:.1f} ms |"
        )
        lines.append(row)

    lines.extend(
        [
            "",
            "## Failure & Ambiguity Analysis",
            "",
        ]
    )

    failed_scenarios = [
        r for r in summary.results if not r.top1_correct or not r.evidence_grounded
    ]
    if not failed_scenarios:
        lines.append(
            "All evaluated benchmark scenarios met Top-1 accuracy "
            "and evidence grounding criteria with zero hallucinations."
        )
    else:
        for f in failed_scenarios:
            causes_str = (
                ", ".join(f.predicted_root_causes)
                if f.predicted_root_causes
                else "None"
            )
            grounded_str = "Yes" if f.evidence_grounded else "No"
            diag_str = f.failure_explanation or "Primary cause ranked outside Top-1."
            lines.extend(
                [
                    f"### Scenario {f.scenario_id}: {f.scenario_name}",
                    "",
                    f"- **Difficulty**: `{f.difficulty}`",
                    f"- **Expected Cause**: `{f.ground_truth_primary}`",
                    f"- **Predicted Causes**: {causes_str}",
                    f"- **MRR Score**: {f.reciprocal_rank:.4f}",
                    f"- **Evidence Grounded**: {grounded_str}",
                    f"- **Diagnosis**: {diag_str}",
                    f"- **Stopping Reason**: {f.stopping_reason}",
                    "",
                ]
            )

    return "\n".join(lines)


def run_scenario(scenario: GroundTruthScenario, conn: Any = None) -> EvaluationResult:
    """Execute a single scenario against the investigation agent and evaluate."""
    request = InvestigationAgentRequest(
        metric=scenario.target_metric,
        anomaly_date=scenario.anomaly_date,
        comparison_days=scenario.comparison_days,
        dimensions=scenario.affected_dimensions
        or ["product_category", "customer_state", "seller"],
        max_investigation_steps=6,
        minimum_contribution_pct=5.0,
    )

    t0 = time.perf_counter()
    if conn is not None:
        agent = AutonomousInvestigationAgent(conn=conn)
        response = agent.run_investigation(request)
    else:
        with get_db_connection() as live_conn:
            agent = AutonomousInvestigationAgent(conn=live_conn)
            response = agent.run_investigation(request)

    execution_time_ms = (time.perf_counter() - t0) * 1000.0

    return evaluate_scenario_response(
        scenario=scenario,
        response=response,
        execution_time_ms=execution_time_ms,
    )


def run_benchmark(
    scenario_id: str | None = None,
    difficulty: str | None = None,
    limit: int | None = None,
    output_json: str | None = None,
    output_md: str | None = None,
    verbose: bool = False,
    conn: Any = None,
) -> BenchmarkSummary:
    """Run the complete benchmark suite or a selected scenario."""
    if scenario_id:
        scenarios = [get_scenario(scenario_id)]
    else:
        scenarios = get_all_scenarios()
        if difficulty and difficulty.lower() in {"easy", "medium", "hard"}:
            scenarios = [
                s for s in scenarios if s.difficulty.lower() == difficulty.lower()
            ]
        if limit and limit > 0:
            scenarios = scenarios[:limit]

    results: list[EvaluationResult] = []

    print("\n========================================================")
    print(" RootCause AI — Forensic Benchmark Evaluation (Phase B)")
    print(f" Scenarios to execute: {len(scenarios)}")
    print("========================================================\n")

    for idx, scn in enumerate(scenarios, 1):
        print(
            f"[{idx}/{len(scenarios)}] Running"
            f" {scn.scenario_id} ({scn.difficulty}): {scn.name}...",
            end="",
            flush=True,
        )
        try:
            res = run_scenario(scn, conn=conn)
            results.append(res)
            status_tag = (
                "PASS (Top-1)"
                if res.top1_correct
                else ("PASS (Top-3)" if res.top3_correct else "FAIL")
            )
            print(f" {status_tag} ({res.execution_time_ms:.1f}ms)")
            if verbose:
                top_cause_str = (
                    res.predicted_root_causes[0]
                    if res.predicted_root_causes
                    else "None"
                )
                print(f"   Ground Truth: {res.ground_truth_primary}")
                print(f"   Top Cause:    {top_cause_str}")
                print(
                    f"   MRR:          {res.reciprocal_rank:.4f} | "
                    f"Steps: {res.investigation_steps}"
                )
        except Exception as e:
            print(f" ERROR: {e}")
            logger.error(f"Error evaluating {scn.scenario_id}: {e}", exc_info=True)
            results.append(
                EvaluationResult(
                    scenario_id=scn.scenario_id,
                    scenario_name=scn.name,
                    ground_truth_primary=scn.primary_cause.cause_id,
                    top1_correct=False,
                    top3_correct=False,
                    reciprocal_rank=0.0,
                    difficulty=scn.difficulty,
                    failure_explanation=f"Execution error: {e}",
                )
            )

    summary = aggregate_benchmark_results(results)

    # Print Console Summary
    print("\n========================================================")
    print(" RootCause AI Benchmark Summary")
    print("========================================================")
    print(f" Total Scenarios:         {summary.scenarios_evaluated}")
    print(f" Top-1 Accuracy:          {summary.top1_accuracy:.1f}%")
    print(f" Top-3 Accuracy:          {summary.top3_accuracy:.1f}%")
    print(f" Mean Reciprocal Rank:    {summary.mrr:.4f}")
    print(f" Evidence Grounding Rate: {summary.evidence_grounding_rate:.1f}%")
    print(f" Hallucination Rate:      {summary.hallucination_rate:.3f} (Zero Target)")
    print(f" Avg Latency:             {summary.avg_execution_time_ms:.1f} ms")
    print("--------------------------------------------------------")
    print(" Performance by Difficulty Tier:")
    if summary.easy_count > 0 and summary.easy_top1_accuracy is not None:
        print(
            f"   Easy   ({summary.easy_count:2d} scenarios): Top-1 = {summary.easy_top1_accuracy:5.1f}% | MRR = {summary.easy_mrr:.4f}"
        )
    if summary.medium_count > 0 and summary.medium_top1_accuracy is not None:
        print(
            f"   Medium ({summary.medium_count:2d} scenarios): Top-1 = {summary.medium_top1_accuracy:5.1f}% | MRR = {summary.medium_mrr:.4f}"
        )
    if summary.hard_count > 0 and summary.hard_top1_accuracy is not None:
        print(
            f"   Hard   ({summary.hard_count:2d} scenarios): Top-1 = {summary.hard_top1_accuracy:5.1f}% | MRR = {summary.hard_mrr:.4f}"
        )
    print("========================================================\n")

    # Generate Reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    md_path = Path(output_md) if output_md else REPORTS_DIR / "latest_benchmark.md"
    md_content = generate_markdown_report(summary)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Saved Markdown Report: {md_path}")

    json_path = (
        Path(output_json) if output_json else REPORTS_DIR / "latest_benchmark.json"
    )
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(summary.model_dump_json(indent=2))
    print(f"[OK] Saved JSON Report:     {json_path}\n")

    return summary


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="RootCause AI Benchmark Evaluation Runner"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Run a specific scenario ID (e.g. SCN-001)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default=None,
        choices=["easy", "medium", "hard", "all"],
        help="Filter scenarios by difficulty tier",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of scenarios to evaluate",
    )
    parser.add_argument(
        "--output-json", type=str, default=None, help="Path for JSON report"
    )
    parser.add_argument(
        "--output-md", type=str, default=None, help="Path for Markdown report"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed scenario trace"
    )
    args = parser.parse_args()

    run_benchmark(
        scenario_id=args.scenario,
        difficulty=args.difficulty if args.difficulty != "all" else None,
        limit=args.limit,
        output_json=args.output_json,
        output_md=args.output_md,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
