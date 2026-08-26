"""CLI Runner for Baseline vs Improved Agent Experiment (Phase I)."""

import argparse
import logging

from apps.api.db.connection import get_db_connection
from evaluation.experiments.comparison import (
    run_comparison_experiment,
    save_comparison_reports,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evaluation.agent_comparison")


def main() -> None:
    """Run baseline vs improved agent comparison benchmark."""
    parser = argparse.ArgumentParser(
        description="Run RootCause AI Baseline vs Improved Agent Experiment"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print detailed execution progress and summary tables",
    )
    args = parser.parse_args()

    print("\n========================================================")
    print(" RootCause AI — Baseline vs Improved Agent Experiment")
    print(" Canonical Scenarios: 6 (SCN-001 ... SCN-006)")
    print("========================================================\n")

    with get_db_connection() as conn:
        summary = run_comparison_experiment(conn=conn, verbose=args.verbose)

    save_comparison_reports(summary)

    if args.verbose:
        b_top1 = summary.baseline_top1_accuracy
        i_top1 = summary.improved_top1_accuracy
        b_top3 = summary.baseline_top3_accuracy
        i_top3 = summary.improved_top3_accuracy
        b_mrr = summary.baseline_mrr
        i_mrr = summary.improved_mrr
        b_fpr = summary.baseline_false_positive_rate
        i_fpr = summary.improved_false_positive_rate
        b_grd = summary.baseline_evidence_grounding_rate
        i_grd = summary.improved_evidence_grounding_rate
        b_c_grd = summary.baseline_claim_grounding_rate
        i_c_grd = summary.improved_claim_grounding_rate
        b_hal = summary.baseline_hallucination_rate
        i_hal = summary.improved_hallucination_rate
        b_num = summary.baseline_numerical_accuracy
        i_num = summary.improved_numerical_accuracy
        b_adv = summary.baseline_adversarial_detection_rate
        i_adv = summary.improved_adversarial_detection_rate
        b_lat = summary.baseline_avg_latency_ms
        i_lat = summary.improved_avg_latency_ms

        print("\n========================================================")
        print(" Aggregate Experiment Summary")
        print("========================================================")
        print(f" Scenarios Evaluated:         {summary.scenarios_evaluated}")
        print(f" Top-1 Accuracy:             Base {b_top1:.1f}% -> Imp {i_top1:.1f}%")
        print(f" Top-3 Accuracy:             Base {b_top3:.1f}% -> Imp {i_top3:.1f}%")
        print(f" Mean Reciprocal Rank (MRR): Base {b_mrr:.4f} -> Imp {i_mrr:.4f}")
        print(f" False Positive Rate:        Base {b_fpr:.3f} -> Imp {i_fpr:.3f}")
        print(f" Evidence Grounding:         Base {b_grd:.1f}% -> Imp {i_grd:.1f}%")
        print(f" Claim Grounding:            Base {b_c_grd:.1f}% -> Imp {i_c_grd:.1f}%")
        print(f" Hallucination Rate:         Base {b_hal:.1f}% -> Imp {i_hal:.1f}%")
        print(f" Numerical Accuracy:         Base {b_num:.1f}% -> Imp {i_num:.1f}%")
        print(f" Adversarial Detection:      Base {b_adv:.1f}% -> Imp {i_adv:.1f}%")
        print(f" Execution Latency:          Base {b_lat:.1f}ms -> Imp {i_lat:.1f}ms")
        print("========================================================\n")


if __name__ == "__main__":
    main()
