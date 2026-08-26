"""CLI Runner for Statistical Change-Point Detection Benchmark (Phase J)."""

import argparse
import logging

from evaluation.change_point.evaluator import (
    run_change_point_benchmark,
    save_change_point_reports,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evaluation.change_point")


def main() -> None:
    """Run change-point detection evaluation benchmark."""
    parser = argparse.ArgumentParser(
        description="Run RootCause AI Statistical Change-Point Evaluation"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print detailed execution progress and summary tables",
    )
    args = parser.parse_args()

    print("\n========================================================")
    print(" RootCause AI — Statistical Change-Point Benchmark (Phase J)")
    print(" Scenarios: 7 Synthetic Regime Dynamics")
    print("========================================================\n")

    summary = run_change_point_benchmark(verbose=args.verbose)
    save_change_point_reports(summary)

    if args.verbose:
        print("\n========================================================")
        print(" Change-Point Benchmark Summary")
        print("========================================================")
        print(f" Scenarios Evaluated:         {summary.scenarios_evaluated}")
        print(f" Classification Accuracy:     {summary.classification_accuracy:.1f}%")
        print(f" Precision:                   {summary.precision:.1f}%")
        print(f" Recall:                      {summary.recall:.1f}%")
        print(f" False Positive Rate:         {summary.false_positive_rate:.1f}%")
        print(
            f" Mean Detection Delay:       {summary.mean_detection_delay_days:.1f} days"
        )
        print(f" Mean Shift Estimation MAE:  {summary.mean_shift_estimation_mae:.2f}%")
        print(f" Variance Shift Accuracy:    {summary.variance_shift_accuracy:.1f}%")
        print(
            f" Insufficient Data Handling: "
            f"{summary.insufficient_data_handling_rate:.1f}%"
        )
        print("========================================================\n")


if __name__ == "__main__":
    main()
