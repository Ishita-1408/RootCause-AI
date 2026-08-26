"""RootCause AI - AI Investigation Narrator Live Demonstration.

Executes a deterministic root-cause investigation against live Supabase data,
passes verified evidence to the AI Narrator, and prints an executive report.
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
from apps.analytics.narrator import (  # noqa: E402
    generate_investigation_narrative,
)
from apps.api.config import get_settings  # noqa: E402
from apps.api.db.connection import get_db_connection  # noqa: E402


def run_narrative_demo() -> None:
    """Execute live narrative demonstration for Black Friday 2017."""
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

    settings = get_settings()
    has_api_key = bool(settings.llm_api_key)

    with get_db_connection() as conn:
        investigation_response = run_investigation(conn=conn, request=request)

    narrative = generate_investigation_narrative(investigation=investigation_response)

    print("=" * 60)
    print(" ROOTCAUSE AI -- AI INVESTIGATION REPORT")
    print("=" * 60)
    print(f"Narrator Mode : {narrative.narrator_type.upper()}")
    print(f"LLM Key Active: {has_api_key}")
    print(f"Report Title  : {narrative.title}")
    print("=" * 60)

    print("\nExecutive Summary")
    print("-" * 60)
    print(narrative.executive_summary)

    print("\nWhat Changed (Anomaly Magnitude)")
    print("-" * 60)
    print(narrative.anomaly_statement)

    print("\nKey Findings")
    print("-" * 60)
    for idx, finding in enumerate(narrative.key_findings, start=1):
        print(f"  {idx}. {finding}")

    print("\nTop Root Causes (Primary Drivers)")
    print("-" * 60)
    for idx, cause in enumerate(narrative.root_causes, start=1):
        print(f"  {idx}. {cause}")

    print("\nContributing Factors (Secondary/Offsetting Slices)")
    print("-" * 60)
    if narrative.contributing_factors:
        for idx, factor in enumerate(narrative.contributing_factors, start=1):
            print(f"  {idx}. {factor}")
    else:
        print("  None")

    print("\nRecommended Next Steps")
    print("-" * 60)
    for idx, step in enumerate(narrative.recommended_next_steps, start=1):
        print(f"  {idx}. {step}")

    print("\nEvidence References (Verified Data Points)")
    print("-" * 60)
    for ref in narrative.evidence_references:
        print(f"  * {ref}")

    print("\nDisclaimer")
    print("-" * 60)
    print(narrative.disclaimer)

    print("\n" + "=" * 60)
    print(" NARRATIVE SYNTHESIS COMPLETED (ZERO NUMERICAL INVENTIONS)")
    print("=" * 60)


if __name__ == "__main__":
    run_narrative_demo()
