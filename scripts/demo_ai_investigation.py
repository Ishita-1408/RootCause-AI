"""RootCause AI - AI Investigation & Executive Summary Demonstration.

Executes a live investigation against Supabase data for the Black Friday 2017 anomaly,
then passes the structured deterministic evidence to the AI Explanation Layer.
"""

import os
import sys
from datetime import date
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.ai import investigate_with_ai  # noqa: E402
from apps.analytics.rootcause import (  # noqa: E402
    RootCauseInvestigationRequest,
    investigate_root_cause,
)
from apps.api.db.connection import get_db_connection  # noqa: E402


def run_ai_demo() -> None:
    """Run end-to-end deterministic + AI investigation."""
    api_key_configured = bool(os.environ.get("LLM_API_KEY", "").strip())
    if not api_key_configured:
        print("\n" + "!" * 60)
        print(" NOTE: LLM_API_KEY is not configured in the environment.")
        print(" Running with the built-in Deterministic Rule Synthesizer.")
        print(" To use an external LLM, export LLM_API_KEY=your_key.")
        print("!" * 60)

    # 1. Run deterministic root-cause investigation
    req = RootCauseInvestigationRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        dimensions=["product_category", "customer_state", "seller"],
        max_results=5,
    )

    with get_db_connection() as conn:
        root_cause_resp = investigate_root_cause(conn=conn, request=req)

    # 2. Run AI Explanation layer
    ai_resp = investigate_with_ai(root_cause_response=root_cause_resp)

    # 3. Print Executive Report
    print("\n" + "=" * 60)
    print(" ROOTCAUSE AI - EXECUTIVE INVESTIGATION")
    print("=" * 60)
    print(f"Title: {ai_resp.investigation_title}")
    print(f"Model: {ai_resp.model} | Fallback Mode: {ai_resp.is_fallback}")

    print("\nExecutive Summary")
    print("-" * 60)
    print(ai_resp.executive_summary)

    print("\nKey Findings")
    print("-" * 60)
    for idx, finding in enumerate(ai_resp.key_findings, start=1):
        print(f"{idx}. {finding}")

    print("\nBusiness Interpretation")
    print("-" * 60)
    for idx, interp in enumerate(ai_resp.business_interpretation, start=1):
        print(f"{idx}. {interp}")

    print("\nRecommended Actions")
    print("-" * 60)
    for idx, action in enumerate(ai_resp.recommended_actions, start=1):
        print(f"{idx}. {action}")

    print("\nLimitations")
    print("-" * 60)
    for limit in ai_resp.limitations:
        print(f"• {limit}")

    print("\n" + "=" * 60)
    print(" EXECUTIVE MEMO COMPLETE (NUMERICAL INTEGRITY PRESERVED)")
    print("=" * 60)


if __name__ == "__main__":
    run_ai_demo()
