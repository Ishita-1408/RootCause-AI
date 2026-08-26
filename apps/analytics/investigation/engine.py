"""Deterministic Root-Cause Contribution Engine for RootCause AI.

Orchestrates multi-dimensional period-over-period contribution analyses,
calculating exact slice deltas, unclamped contribution shares, and ranking
top positive vs. negative drivers.
"""

from datetime import date
from typing import Literal, TypedDict

import psycopg

from apps.analytics.investigation.models import (
    ContributionAnalysis,
    Contributor,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationSummary,
)
from apps.analytics.investigation.queries import (
    SUPPORTED_DIMENSIONS,
    SUPPORTED_METRICS,
    DimensionSliceRecord,
    fetch_metric_by_dimension,
)


class _RawEntry(TypedDict):
    value: str
    current_value: float
    baseline_value: float
    absolute_change: float
    percentage_change: float | None
    contribution_pct: float | None


def calculate_slice_metrics(
    slices: list[DimensionSliceRecord],
    dimension_name: str,
    limit: int = 10,
) -> tuple[
    float,
    float,
    float,
    float | None,
    list[Contributor],
    list[Contributor],
]:
    """Pure mathematical contribution calculation and ranking logic.

    Calculates:
        - Total current, baseline, absolute change, and percentage change
        - Slice-level absolute change and percentage change
        - Unclamped mathematical contribution percentage: (diff_i / total_diff) * 100
        - Separate ranking for positive (growth) and negative (decline) contributors
    """
    tot_cur = round(sum(s["current_value"] for s in slices), 4)
    tot_base = round(sum(s["baseline_value"] for s in slices), 4)
    tot_change = round(tot_cur - tot_base, 4)

    tot_change_pct: float | None = None
    if tot_base > 0:
        tot_change_pct = round((tot_change / tot_base) * 100.0, 2)
    elif tot_base == 0 and tot_cur > 0:
        tot_change_pct = 100.0
    elif tot_base == 0 and tot_cur == 0:
        tot_change_pct = 0.0

    pos_raw: list[_RawEntry] = []
    neg_raw: list[_RawEntry] = []

    for s in slices:
        c_val = s["current_value"]
        b_val = s["baseline_value"]
        diff = round(c_val - b_val, 4)

        pct_change: float | None = None
        if b_val > 0:
            pct_change = round((diff / b_val) * 100.0, 2)
        elif b_val == 0 and c_val > 0:
            pct_change = 100.0
        elif b_val == 0 and c_val == 0:
            pct_change = 0.0

        contrib_pct: float | None = None
        if tot_change != 0:
            contrib_pct = round((diff / tot_change) * 100.0, 2)

        entry: _RawEntry = {
            "value": s["slice_value"],
            "current_value": round(c_val, 2),
            "baseline_value": round(b_val, 2),
            "absolute_change": round(diff, 2),
            "percentage_change": pct_change,
            "contribution_pct": contrib_pct,
        }

        if diff > 0:
            pos_raw.append(entry)
        elif diff < 0:
            neg_raw.append(entry)

    # Sort positive contributors by largest positive change (descending)
    pos_raw.sort(key=lambda x: x["absolute_change"], reverse=True)
    # Sort negative contributors by most negative change (ascending)
    neg_raw.sort(key=lambda x: x["absolute_change"])

    top_positive: list[Contributor] = []
    for rank_idx, item in enumerate(pos_raw[:limit], start=1):
        top_positive.append(
            Contributor(
                dimension=dimension_name,
                value=item["value"],
                current_value=item["current_value"],
                baseline_value=item["baseline_value"],
                absolute_change=item["absolute_change"],
                percentage_change=item["percentage_change"],
                contribution_pct=item["contribution_pct"],
                rank=rank_idx,
            )
        )

    top_negative: list[Contributor] = []
    for rank_idx, item in enumerate(neg_raw[:limit], start=1):
        top_negative.append(
            Contributor(
                dimension=dimension_name,
                value=item["value"],
                current_value=item["current_value"],
                baseline_value=item["baseline_value"],
                absolute_change=item["absolute_change"],
                percentage_change=item["percentage_change"],
                contribution_pct=item["contribution_pct"],
                rank=rank_idx,
            )
        )

    return (
        round(tot_cur, 2),
        round(tot_base, 2),
        round(tot_change, 2),
        tot_change_pct,
        top_positive,
        top_negative,
    )


def run_contribution_analysis(
    conn: psycopg.Connection,
    metric: str,
    dimension: str,
    current_start: date,
    current_end: date,
    baseline_start: date,
    baseline_end: date,
    limit: int = 10,
) -> ContributionAnalysis:
    """Execute contribution analysis for a single dimension."""
    norm_metric = metric.strip().lower()
    norm_dim = dimension.strip().lower()

    if norm_metric not in SUPPORTED_METRICS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Supported: {SUPPORTED_METRICS}"
        )
    if norm_dim not in SUPPORTED_DIMENSIONS:
        raise ValueError(
            f"Unsupported dimension '{dimension}'. Supported: {SUPPORTED_DIMENSIONS}"
        )

    slices = fetch_metric_by_dimension(
        conn=conn,
        metric=norm_metric,
        dimension=norm_dim,
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
    )

    tot_cur, tot_base, tot_change, tot_change_pct, top_pos, top_neg = (
        calculate_slice_metrics(
            slices=slices,
            dimension_name=norm_dim,
            limit=limit,
        )
    )

    return ContributionAnalysis(
        metric=norm_metric,
        dimension=norm_dim,
        current_start=current_start,
        current_end=current_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        total_current=tot_cur,
        total_baseline=tot_base,
        total_change=tot_change,
        total_change_pct=tot_change_pct,
        top_negative_contributors=top_neg,
        top_positive_contributors=top_pos,
        all_contributors_count=len(slices),
    )


def run_investigation(
    conn: psycopg.Connection,
    request: InvestigationRequest,
) -> InvestigationResponse:
    """Run multi-dimensional root-cause investigation across dimensions."""
    analyses: list[ContributionAnalysis] = []

    for dim in request.dimensions:
        analysis = run_contribution_analysis(
            conn=conn,
            metric=request.metric,
            dimension=dim,
            current_start=request.current_start,
            current_end=request.current_end,
            baseline_start=request.baseline_start,
            baseline_end=request.baseline_end,
        )
        analyses.append(analysis)

    # Calculate headline summary from first analysis
    first_analysis = analyses[0] if analyses else None
    tot_cur = first_analysis.total_current if first_analysis else 0.0
    tot_base = first_analysis.total_baseline if first_analysis else 0.0
    tot_change = first_analysis.total_change if first_analysis else 0.0
    tot_change_pct = first_analysis.total_change_pct if first_analysis else None

    direction: Literal["increase", "decrease", "unchanged", "undefined"] = "unchanged"
    if tot_change > 0:
        direction = "increase"
    elif tot_change < 0:
        direction = "decrease"

    # Identify primary driving dimension and contributor
    primary_neg_dim: str | None = None
    primary_neg_val: str | None = None
    primary_pos_dim: str | None = None
    primary_pos_val: str | None = None

    most_negative_val = 0.0
    most_positive_val = 0.0

    for a in analyses:
        if a.top_negative_contributors:
            top_neg = a.top_negative_contributors[0]
            if top_neg.absolute_change < most_negative_val:
                most_negative_val = top_neg.absolute_change
                primary_neg_dim = a.dimension
                primary_neg_val = top_neg.value

        if a.top_positive_contributors:
            top_pos = a.top_positive_contributors[0]
            if top_pos.absolute_change > most_positive_val:
                most_positive_val = top_pos.absolute_change
                primary_pos_dim = a.dimension
                primary_pos_val = top_pos.value

    summary = InvestigationSummary(
        metric=request.metric,
        direction=direction,
        total_current=tot_cur,
        total_baseline=tot_base,
        total_change=tot_change,
        total_change_pct=tot_change_pct,
        primary_negative_dimension=primary_neg_dim,
        primary_negative_contributor=primary_neg_val,
        primary_positive_dimension=primary_pos_dim,
        primary_positive_contributor=primary_pos_val,
    )

    return InvestigationResponse(
        request=request,
        summary=summary,
        analyses=analyses,
    )
