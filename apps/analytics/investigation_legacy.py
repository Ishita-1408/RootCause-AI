"""RootCause AI - Legacy Revenue Investigation Orchestration Engine."""

import psycopg

from apps.analytics.models import (
    RevenueInvestigationRequest,
    RevenueInvestigationResponse,
)
from apps.analytics.revenue_analysis import (
    analyze_dimension_breakdown,
    compute_change_metrics,
    fetch_period_summary,
)


def run_revenue_investigation(
    request: RevenueInvestigationRequest, conn: psycopg.Connection
) -> RevenueInvestigationResponse:
    """Execute a deterministic period-over-period revenue investigation."""
    current_summary = fetch_period_summary(conn, request.start_date, request.end_date)
    baseline_summary = fetch_period_summary(
        conn, request.baseline_start_date, request.baseline_end_date
    )

    change = compute_change_metrics(current_summary, baseline_summary)

    dimensions = [
        "customer_state",
        "product_category",
        "seller",
        "order_status",
    ]
    all_findings = []

    for dim in dimensions:
        findings = analyze_dimension_breakdown(
            conn=conn,
            dimension=dim,
            start_date=request.start_date,
            end_date=request.end_date,
            baseline_start=request.baseline_start_date,
            baseline_end=request.baseline_end_date,
            total_revenue_change=change.revenue_change,
            limit=5,
        )
        all_findings.extend(findings)

    return RevenueInvestigationResponse(
        metric="revenue",
        current_period=current_summary,
        baseline_period=baseline_summary,
        change=change,
        findings=all_findings,
    )
