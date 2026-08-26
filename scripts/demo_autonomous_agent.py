"""Demonstration script for Phase 8 Autonomous Investigation Agent."""

import sys
from datetime import date
from pathlib import Path

# Ensure workspace root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.analytics.agent import (  # noqa: E402
    InvestigationAgentRequest,
    run_autonomous_investigation,
)
from apps.api.db.connection import get_db_connection  # noqa: E402


def main() -> None:
    print("=" * 65)
    print(" ROOTCAUSE AI -- AUTONOMOUS INVESTIGATION AGENT")
    print("=" * 65)

    request = InvestigationAgentRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        dimensions=["product_category", "customer_state", "seller"],
        max_investigation_steps=6,
        minimum_contribution_pct=5.0,
    )

    print(
        f"\n[INIT] Initiating Autonomous Investigation for {request.metric.upper()} "
        f"on {request.anomaly_date}..."
    )

    with get_db_connection() as conn:
        response = run_autonomous_investigation(conn=conn, request=request)

    print("\n------------------------------------------------------------")
    print(" ANOMALY HEADLINE SUMMARY")
    print("------------------------------------------------------------")
    s = response.anomaly_summary
    print(f"Metric:           {s.metric.upper()}")
    print(f"Anomaly Date:     {s.anomaly_date}")
    print(f"Baseline Window:  {s.baseline_start_date} to {s.baseline_end_date}")
    print(f"Observed Value:   R$ {s.observed_value:,.2f}")
    print(f"Baseline Value:   R$ {s.baseline_value:,.2f}")
    print(
        f"Absolute Change:  R$ {s.absolute_change:+,.2f} ({s.percentage_change:+.1f}%)"
    )

    print("\n------------------------------------------------------------")
    print(" INVESTIGATION TRACE (AUDIT TRAIL)")
    print("------------------------------------------------------------")
    for trace in response.trace:
        status_tag = f"[{trace.status.upper()}]"
        print(f"\nStep {trace.step_number}: {trace.step_title} {status_tag}")
        if trace.status == "completed":
            print(f"  Finding: {trace.finding_summary}")
        elif trace.status == "skipped":
            print(f"  Reason:  {trace.reason_if_skipped}")

    print("\n------------------------------------------------------------")
    print(" TOP RANKED ROOT CAUSES")
    print("------------------------------------------------------------")
    for rc in response.top_root_causes:
        print(
            f"#{rc.rank} {rc.title:<35} | Share: {rc.contribution_pct:>+6.1f}% | "
            f"Delta: R$ {rc.absolute_change:>+10,.2f} | Score: {rc.score:>6.1f}"
        )
        print(f"   -> {rc.explanation}")

    print("\n------------------------------------------------------------")
    print(" TERMINATION STATUS")
    print("------------------------------------------------------------")
    print(f"Status: {response.investigation_status.upper()}")
    print(f"Reason: {response.termination_reason}")

    print("\n------------------------------------------------------------")
    print(" EXECUTIVE DECISION MEMO (AI EXPLANATION LAYER)")
    print("------------------------------------------------------------")
    print(f"Summary:\n{response.executive_summary}\n")
    print("Key Findings:")
    for f in response.key_findings:
        print(f" - {f}")
    print("\nRecommended Actions:")
    for a in response.recommended_actions:
        print(f" -> {a}")

    print("\n" + "=" * 65)
    print(" AUTONOMOUS INVESTIGATION COMPLETE (100% GROUNDED NUMBERS)")
    print("=" * 65)


if __name__ == "__main__":
    main()
