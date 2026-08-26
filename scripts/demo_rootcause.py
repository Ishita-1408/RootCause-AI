"""RootCause AI - Deterministic Root-Cause Investigation Live Demonstration.

Executes a drill-down root-cause investigation against live Supabase data
for the Black Friday 2017 anomaly (2017-11-24).
"""

import sys
from datetime import date
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.analytics.rootcause import (  # noqa: E402
    RootCauseInvestigationRequest,
    investigate_root_cause,
)
from apps.api.db.connection import get_db_connection  # noqa: E402
from scripts.eda_helpers import format_currency_brl  # noqa: E402


def run_demo() -> None:
    """Execute live RootCause investigation."""
    req = RootCauseInvestigationRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        dimensions=["product_category", "customer_state", "seller"],
        max_results=10,
    )

    with get_db_connection() as conn:
        res = investigate_root_cause(conn=conn, request=req)

    print("=" * 60)
    print(" ROOTCAUSE AI INVESTIGATION")
    print("=" * 60)
    print(f"Anomaly Date: {res.summary.anomaly_date}")
    print(f"Metric      : {res.summary.metric.replace('_', ' ').title()}")

    pct_str = (
        f"{res.summary.percentage_change:+.1f}%"
        if res.summary.percentage_change is not None
        else "N/A"
    )
    obs_gmv_str = format_currency_brl(res.summary.observed_value)
    base_gmv_str = format_currency_brl(res.summary.baseline_value)
    print(f"\nObserved GMV:       {obs_gmv_str}")
    print(f"Baseline GMV:       {base_gmv_str}")
    print(f"Change:             {pct_str}")
    print("Severity:           CRITICAL")

    if res.decomposition:
        orders_pct = "N/A"
        if res.decomposition.baseline_orders > 0:
            ord_delta = (
                res.decomposition.observed_orders - res.decomposition.baseline_orders
            )
            orders_pct = (
                f"{(ord_delta / res.decomposition.baseline_orders * 100.0):+.1f}%"
            )

        aov_pct = "N/A"
        if res.decomposition.baseline_aov > 0:
            aov_delta = res.decomposition.observed_aov - res.decomposition.baseline_aov
            aov_pct = f"{(aov_delta / res.decomposition.baseline_aov * 100.0):+.1f}%"

        vol_eff_str = format_currency_brl(res.decomposition.volume_effect)
        aov_eff_str = format_currency_brl(res.decomposition.aov_effect)
        inter_eff_str = format_currency_brl(res.decomposition.interaction_effect)

        print("\nVOLUME VS VALUE")
        print("-" * 60)
        print(f"Orders:             {orders_pct}")
        print(f"AOV:                {aov_pct}")
        print(f"Volume Effect:      {vol_eff_str}")
        print(f"AOV Effect:         {aov_eff_str}")
        print(f"Interaction Effect: {inter_eff_str}")

    print("\nTOP CONTRIBUTORS")
    print("-" * 60)
    for idx, c in enumerate(res.ranked_contributors[:5], start=1):
        c_pct = (
            f"{c.contribution_pct:.1f}%" if c.contribution_pct is not None else "N/A"
        )
        dim_title = c.dimension.replace("_", " ").title()
        c_delta_str = format_currency_brl(c.absolute_change)
        print(f"{idx}. {dim_title}: {c.dimension_value}")
        print(f"   Delta: {c_delta_str} | Contribution: {c_pct}\n")

    op_late = res.operational_indicators.observed_late_delivery_rate
    op_days = res.operational_indicators.observed_avg_delivery_days
    op_rev = res.operational_indicators.observed_avg_review_score

    print("OPERATIONAL SIGNALS")
    print("-" * 60)
    print(f"Late Delivery Rate: {op_late:.1f}%")
    print(f"Average Delivery:   {op_days:.1f} days")
    print(f"Average Review:     {op_rev:.2f}")

    print("\nROOT-CAUSE SUMMARY")
    print("-" * 60)
    print(res.explanation)

    print("\n" + "=" * 60)
    print(" INVESTIGATION COMPLETED DETERMINISTICALLY")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
