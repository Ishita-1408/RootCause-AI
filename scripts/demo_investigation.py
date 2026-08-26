"""RootCause AI - Live Root-Cause Contribution Investigation Demo.

Runs a multi-dimensional contribution analysis against live Supabase PostgreSQL data.
"""

import sys
from datetime import date
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.analytics.investigation import (  # noqa: E402
    InvestigationRequest,
    run_investigation,
)
from apps.api.db.connection import get_db_connection  # noqa: E402
from scripts.eda_helpers import format_currency_brl  # noqa: E402


def run_demo() -> None:
    """Execute live demo comparing Black Friday 2017 vs prior week baseline."""
    request = InvestigationRequest(
        metric="total_gmv",
        current_start=date(2017, 11, 24),
        current_end=date(2017, 11, 24),
        baseline_start=date(2017, 11, 17),
        baseline_end=date(2017, 11, 17),
        dimensions=[
            "product_category_name",
            "customer_state",
            "payment_type",
        ],
    )

    print("=" * 60)
    print(" ROOTCAUSE AI INVESTIGATION DEMO")
    print("=" * 60)

    with get_db_connection() as conn:
        response = run_investigation(conn=conn, request=request)

    print(f"\nMetric          : {response.summary.metric.upper()}")
    print(f"Current period  : {request.current_start} to {request.current_end}")
    print(f"Baseline period : {request.baseline_start} to {request.baseline_end}")
    print(f"Total current   : {format_currency_brl(response.summary.total_current)}")
    print(f"Total baseline  : {format_currency_brl(response.summary.total_baseline)}")

    pct_str = (
        f"{response.summary.total_change_pct:+.2f}%"
        if response.summary.total_change_pct is not None
        else "N/A"
    )
    chg_val = format_currency_brl(response.summary.total_change)
    print(f"Change          : {chg_val} ({pct_str})")
    print(f"Direction       : {response.summary.direction.upper()}")

    for analysis in response.analyses:
        dim_title = analysis.dimension.replace("_", " ").upper()
        print("\n" + "-" * 60)
        cnt = analysis.all_contributors_count
        print(f" DIMENSION: {dim_title} (Evaluated {cnt} slices)")
        print("-" * 60)

        print("\n  [TOP POSITIVE CONTRIBUTORS (GROWTH DRIVERS)]:")
        if analysis.top_positive_contributors:
            for item in analysis.top_positive_contributors[:5]:
                chg_str = format_currency_brl(item.absolute_change)
                contrib_str = (
                    f"{item.contribution_pct:.2f}%"
                    if item.contribution_pct is not None
                    else "N/A"
                )
                val_str = f"{item.rank}. {item.value:<30}"
                print(
                    f"    {val_str} | Change: +{chg_str:>14} | "
                    f"Contrib: {contrib_str:>8}"
                )
        else:
            print("    None")

        print("\n  [TOP NEGATIVE CONTRIBUTORS (DECLINE DRIVERS)]:")
        if analysis.top_negative_contributors:
            for item in analysis.top_negative_contributors[:5]:
                chg_str = format_currency_brl(item.absolute_change)
                contrib_str = (
                    f"{item.contribution_pct:.2f}%"
                    if item.contribution_pct is not None
                    else "N/A"
                )
                val_str = f"{item.rank}. {item.value:<30}"
                print(
                    f"    {val_str} | Change: {chg_str:>15} | Contrib: {contrib_str:>8}"
                )
        else:
            print("    None")

    print("\n" + "=" * 60)
    print(" INVESTIGATION COMPLETED DETERMINISTICALLY (100% AUDITABLE)")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
