"""RootCause AI - Automated Root-Cause Diagnostic Engine Demonstration.

Executes 3 real diagnostic investigations against live Supabase PostgreSQL data:
1. Major GMV Surge (Black Friday 2017)
2. Major GMV Decline (Post-Holiday Volume Contraction)
3. Delivery Fulfillment & Quality Operational Anomaly
"""

import sys
from datetime import date
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.analytics.diagnostics import (  # noqa: E402
    DiagnosticRequest,
    DiagnosticResponse,
    run_root_cause_analysis,
)
from apps.api.db.connection import get_db_connection  # noqa: E402
from scripts.eda_helpers import format_currency_brl  # noqa: E402


def print_diagnostic_report(res: DiagnosticResponse, scenario_title: str) -> None:
    """Print structured, executive diagnostic report in console."""
    print("\n" + "=" * 60)
    print(f" ROOTCAUSE AI DIAGNOSTIC REPORT: {scenario_title.upper()}")
    print("=" * 60)

    pct_str = (
        f"{res.summary.percentage_change:+.1f}%"
        if res.summary.percentage_change is not None
        else "N/A"
    )
    cur_val_str = (
        format_currency_brl(res.summary.actual_value)
        if "gmv" in res.request.metric
        else f"{res.summary.actual_value:,.2f}"
    )
    base_val_str = (
        format_currency_brl(res.summary.baseline_value)
        if "gmv" in res.request.metric
        else f"{res.summary.baseline_value:,.2f}"
    )

    print(f"\nTarget Metric   : {res.request.metric.upper()}")
    print(f"Anomaly Date    : {res.request.anomaly_date}")
    w_actual = (
        f"[{res.summary.comparison_period_start}..{res.summary.comparison_period_end}]"
    )
    w_base = f"[{res.summary.baseline_period_start}..{res.summary.baseline_period_end}]"
    print(f"Period Windows  : Actual {w_actual} vs Baseline {w_base}")
    print(f"Actual Value    : {cur_val_str}")
    print(f"Baseline Value  : {base_val_str}")
    print(f"Absolute Delta  : {res.summary.absolute_change:+,.2f} ({pct_str})")
    print(f"PRIMARY DRIVER  : {res.summary.primary_driver}")
    print(f"Confidence Score: {res.summary.confidence_score:.2f}")

    if res.revenue_decomposition:
        print("\nRevenue Decomposition (Exact Additive Identity):")
        print("-" * 60)
        vol_str = format_currency_brl(res.revenue_decomposition.volume_effect)
        aov_str = format_currency_brl(res.revenue_decomposition.aov_effect)
        inter_str = format_currency_brl(res.revenue_decomposition.interaction_effect)
        tot_str = format_currency_brl(res.revenue_decomposition.total_revenue_change)
        vol_pct = res.revenue_decomposition.volume_contribution_pct
        aov_pct = res.revenue_decomposition.aov_contribution_pct
        inter_pct = res.revenue_decomposition.interaction_contribution_pct
        print(f"  Volume Effect     : {vol_str:>16} ({vol_pct}%)")
        print(f"  AOV Effect        : {aov_str:>16} ({aov_pct}%)")
        print(f"  Interaction Effect: {inter_str:>16} ({inter_pct}%)")
        print(f"  Total GMV Change  : {tot_str:>16} (100.0%)")

    print("\nTop Dimensional Contributors:")
    print("-" * 60)
    for idx, d in enumerate(res.top_dimensional_contributors[:6], start=1):
        chg_str = format_currency_brl(d.change)
        c_pct = (
            f"{d.contribution_pct:+.1f}%" if d.contribution_pct is not None else "N/A"
        )
        val_str = f"{idx}. [{d.dimension:<21}] {d.dimension_value:<25}"
        print(f"  {val_str} | Delta: {chg_str:>14} | Share: {c_pct:>7}")

    print("\nOperational & Satisfaction Signals:")
    print("-" * 60)
    for op in res.operational_signals:
        sev_tag = f"[{op.severity.upper()}]"
        print(
            f"  * {op.metric:<24}: {op.baseline_value:.1f} -> "
            f"{op.actual_value:.1f} ({op.change:+.1f}) {sev_tag:>10}"
        )
    for sat in res.satisfaction_signals:
        imp_tag = f"[{sat.sentiment_impact.upper()}]"
        print(
            f"  * {sat.metric:<24}: {sat.baseline_value:.2f} -> "
            f"{sat.actual_value:.2f} ({sat.change:+.2f}) {imp_tag:>10}"
        )

    print("\nRoot Cause Candidate Ranking (Deterministic Multi-Factor Scoring):")
    print("-" * 60)
    for rc in res.root_cause_ranking:
        print(
            f"  {rc.rank}. {rc.cause:<36} | Score: {rc.score:.2f} | "
            f"Category: {rc.category}"
        )
        print(f"     Contribution: {rc.contribution}")
        print(f"     Evidence    : {rc.evidence}")

    print("\nDiagnostic Conclusion:")
    print("-" * 60)
    print(res.conclusion)
    print("=" * 60)


def run_all_demos() -> None:
    """Execute 3 real diagnostic scenarios."""
    with get_db_connection() as conn:
        # Scenario 1: Major GMV Surge (Black Friday Week Nov 2017)
        req1 = DiagnosticRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 24),
            comparison_window=7,
            baseline_window=28,
        )
        res1 = run_root_cause_analysis(conn=conn, request=req1)
        print_diagnostic_report(res1, "1. Major GMV Surge (Black Friday 2017)")

        # Scenario 2: Major GMV Decline (Post-Holiday Contraction Jan 2018)
        req2 = DiagnosticRequest(
            metric="total_gmv",
            anomaly_date=date(2018, 1, 1),
            comparison_window=7,
            baseline_window=28,
        )
        res2 = run_root_cause_analysis(conn=conn, request=req2)
        print_diagnostic_report(res2, "2. Post-Holiday Volume Contraction (Jan 2018)")

        # Scenario 3: Delivery / Quality Operational Anomaly (March 2018)
        req3 = DiagnosticRequest(
            metric="late_delivery_rate_pct",
            anomaly_date=date(2018, 3, 15),
            comparison_window=7,
            baseline_window=28,
        )
        res3 = run_root_cause_analysis(conn=conn, request=req3)
        print_diagnostic_report(res3, "3. Delivery & Fulfillment Anomaly (March 2018)")


if __name__ == "__main__":
    run_all_demos()
