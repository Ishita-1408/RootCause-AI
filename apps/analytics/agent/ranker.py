"""Deterministic evidence ranker with causal separation."""

import math
from typing import Any

from apps.analytics.agent.models import RankedRootCause
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
)


def calculate_root_cause_score(
    contribution_pct: float | None,
    absolute_change: float,
    dimension: str,
    is_causal_mechanism: bool = False,
) -> float:
    """Calculate deterministic attribution score for a candidate root cause."""
    pct = min(abs(float(contribution_pct or 0.0)), 100.0)
    mag = abs(float(absolute_change))

    # Logarithmic magnitude factor: log10(1 + R$ magnitude / 1000)
    mag_factor = 1.0 + math.log10(1.0 + (mag / 1000.0))

    dim_weights = {
        "order_volume": 1.50,
        "average_order_value": 1.45,
        "delivery": 1.60,
        "pricing": 1.40,
        "customer_state": 0.85,
        "product_category": 0.80,
        "seller": 0.75,
    }
    dim_weight = dim_weights.get(dimension, 1.0)
    mechanism_multiplier = 1.30 if is_causal_mechanism else 1.0

    score = pct * mag_factor * dim_weight * mechanism_multiplier
    return round(score, 2)


def rank_evidence(
    contributors: list[DimensionContributor],
    decomposition: Any | None = None,
    summary: AnomalySummary | None = None,
    operational_signals: OperationalIndicators | None = None,
    max_causes: int = 5,
) -> list[RankedRootCause]:
    """Rank all gathered evidence into an ordered list of top root causes.

    Explicitly separates Causal Mechanism (Why) from Affected Segment (Where).
    """
    candidates: list[RankedRootCause] = []

    # Identify top affected geographic/category slice for segment attribution
    top_state_slice = next(
        (c for c in contributors if c.dimension == "customer_state"), None
    )
    top_cat_slice = next(
        (c for c in contributors if c.dimension == "product_category"), None
    )
    primary_affected_segment = top_state_slice or (
        contributors[0] if contributors else None
    )
    affected_dim = (
        primary_affected_segment.dimension if primary_affected_segment else None
    )
    affected_val = (
        primary_affected_segment.dimension_value if primary_affected_segment else None
    )

    target_metric = summary.metric if summary else "total_gmv"

    # 1. Evaluate Macro Revenue Drivers (Volume vs AOV) for revenue/order metrics
    revenue_metrics = {"total_gmv", "orders_count", "average_order_value"}
    if decomposition and target_metric in revenue_metrics:
        vol_pct = getattr(decomposition, "volume_contribution_pct", 0.0) or 0.0
        vol_eff = getattr(decomposition, "volume_effect", 0.0)
        aov_pct = getattr(decomposition, "aov_contribution_pct", 0.0) or 0.0
        aov_eff = getattr(decomposition, "aov_effect", 0.0)
        orders_shift_pct = (
            (
                (decomposition.observed_orders - decomposition.baseline_orders)
                / decomposition.baseline_orders
            )
            * 100.0
            if decomposition.baseline_orders > 0
            else 0.0
        )

        # Volume Driver
        if abs(vol_pct) >= 15.0:
            vol_score = calculate_root_cause_score(
                vol_pct, vol_eff, "order_volume", is_causal_mechanism=True
            )
            vol_dir = "Surge" if vol_eff >= 0 else "Contraction"
            evidence_chain = [
                (
                    f"Order volume shifted {orders_shift_pct:+.1f}% vs "
                    "7-day rolling baseline."
                ),
                (
                    f"Volume change explains {vol_pct:+.1f}% of total "
                    f"GMV variance (R$ {vol_eff:+,.2f})."
                ),
            ]
            if top_state_slice:
                state_pct = top_state_slice.contribution_pct or 0.0
                state_val = top_state_slice.dimension_value
                state_delta = top_state_slice.absolute_change
                evidence_chain.append(
                    f"Growth concentrated in {state_val} ({state_pct:+.1f}% share, "
                    f"R$ {state_delta:+,.2f})."
                )
            evidence_chain.append(
                f"Root Cause: Order Volume {vol_dir} (Verified mart math)."
            )

            candidates.append(
                RankedRootCause(
                    rank=0,
                    title=f"Order Volume {vol_dir}",
                    dimension="order_volume",
                    dimension_value=(
                        f"{decomposition.observed_orders:,.0f} orders "
                        f"(vs {decomposition.baseline_orders:,.0f})"
                    ),
                    contribution_pct=round(vol_pct, 1),
                    absolute_change=round(vol_eff, 2),
                    score=vol_score,
                    explanation=(
                        f"Order volume shifted {orders_shift_pct:+.1f}%, driving "
                        f"R$ {vol_eff:,.2f} of headline movement. "
                        f"Concentrated in {affected_dim}: {affected_val}."
                    ),
                    causal_category="macro_driver",
                    causal_mechanism="order_volume",
                    affected_dimension=affected_dim,
                    affected_value=affected_val,
                    evidence_chain=evidence_chain,
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

        aov_shift_pct = (
            (
                (decomposition.observed_aov - decomposition.baseline_aov)
                / decomposition.baseline_aov
            )
            * 100.0
            if decomposition.baseline_aov > 0
            else 0.0
        )

        # Average Order Value Driver
        if abs(aov_pct) >= 15.0:
            aov_score = calculate_root_cause_score(
                aov_pct, aov_eff, "average_order_value", is_causal_mechanism=True
            )
            aov_dir = "Expansion" if aov_eff >= 0 else "Contraction"
            evidence_chain = [
                (
                    f"Average basket size shifted {aov_shift_pct:+.1f}% vs "
                    "7-day rolling baseline."
                ),
                (
                    f"Basket pricing explains {aov_pct:+.1f}% of total "
                    f"GMV variance (R$ {aov_eff:+,.2f})."
                ),
            ]
            if top_cat_slice:
                cat_val = top_cat_slice.dimension_value
                evidence_chain.append(
                    f"Shift concentrated in product category '{cat_val}'."
                )
            evidence_chain.append(
                f"Root Cause: Average Order Value {aov_dir} (Verified mart math)."
            )

            candidates.append(
                RankedRootCause(
                    rank=0,
                    title=f"Average Order Value {aov_dir}",
                    dimension="average_order_value",
                    dimension_value=(
                        f"R$ {decomposition.observed_aov:.2f} "
                        f"(vs R$ {decomposition.baseline_aov:.2f})"
                    ),
                    contribution_pct=round(aov_pct, 1),
                    absolute_change=round(aov_eff, 2),
                    score=aov_score,
                    explanation=(
                        f"Average basket size shifted {aov_shift_pct:+.1f}%, "
                        f"accounting for R$ {aov_eff:,.2f} of GMV variance."
                    ),
                    causal_category="macro_driver",
                    causal_mechanism="average_order_value",
                    affected_dimension=(
                        top_cat_slice.dimension if top_cat_slice else affected_dim
                    ),
                    affected_value=(
                        top_cat_slice.dimension_value if top_cat_slice else affected_val
                    ),
                    evidence_chain=evidence_chain,
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

    # 2. Evaluate Operational & Delivery Mechanisms (for delivery anomalies)
    if target_metric in ["late_delivery_rate_pct", "delivery"]:
        op = operational_signals
        obs_rate = op.observed_late_delivery_rate if op else 0.0
        base_rate = op.baseline_late_delivery_rate if op else 0.0
        lead_change = op.avg_delivery_days_change if op else 0.0

        evidence_chain = [
            (
                f"Late delivery rate rose to {obs_rate:.1f}% "
                f"(vs {base_rate:.1f}% baseline)."
            ),
            (
                f"Average transit duration expanded by {lead_change:+.1f} "
                "days across routes."
            ),
        ]
        if primary_affected_segment:
            aff_v = primary_affected_segment.dimension_value
            aff_pct = primary_affected_segment.contribution_pct or 0.0
            aff_delta = primary_affected_segment.absolute_change
            evidence_chain.append(
                f"Concentrated in {aff_v} ({aff_pct:+.1f}% share, "
                f"R$ {aff_delta:+,.2f})."
            )
        evidence_chain.append(
            "Root Cause: Carrier SLA & Logistics Fulfillment Degradation "
            "(Verified mart math)."
        )

        delivery_score = calculate_root_cause_score(
            100.0,
            summary.absolute_change if summary else 1000.0,
            "delivery",
            is_causal_mechanism=True,
        )

        candidates.append(
            RankedRootCause(
                rank=0,
                title="Carrier SLA & Logistics Fulfillment Degradation",
                dimension="delivery",
                dimension_value="carrier_transit_delay",
                contribution_pct=100.0,
                absolute_change=round(summary.absolute_change if summary else 0.0, 2),
                score=delivery_score,
                explanation=(
                    f"Late delivery rate rose to {obs_rate:.1f}% vs "
                    f"{base_rate:.1f}% baseline. While impact was "
                    f"concentrated in {affected_dim}: {affected_val}, "
                    "the causal mechanism is carrier delivery deterioration."
                ),
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=affected_dim,
                affected_value=affected_val,
                evidence_chain=evidence_chain,
                evidence_strength="high",
                confidence=1.0,
            )
        )

    # 3. Evaluate Granular Dimensional Slices (Affected Segments)
    for c in contributors:
        pct = c.contribution_pct or 0.0
        score = calculate_root_cause_score(
            pct, c.absolute_change, c.dimension, is_causal_mechanism=False
        )
        dim_label = c.dimension.replace("_", " ").title()

        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"{dim_label}: {c.dimension_value}",
                dimension=c.dimension,
                dimension_value=c.dimension_value,
                contribution_pct=round(pct, 1),
                absolute_change=round(c.absolute_change, 2),
                score=score,
                explanation=(
                    f"Segment slice '{c.dimension_value}' concentrated {pct:+.1f}% "
                    f"(R$ {c.absolute_change:,.2f} delta vs baseline)."
                ),
                causal_category="segment_concentration",
                causal_mechanism=None,
                affected_dimension=c.dimension,
                affected_value=c.dimension_value,
                evidence_chain=[
                    f"Segment {c.dimension}: {c.dimension_value} evaluated.",
                    f"Observed R$ {c.observed_value:,.2f} vs baseline.",
                    f"Mathematical contribution: {pct:+.1f}%.",
                ],
                evidence_strength="high",
                confidence=0.95,
            )
        )

    # Prioritize Causal Mechanisms over pure Segment Concentrations, then sort by score
    mechanisms = [c for c in candidates if c.causal_category != "segment_concentration"]
    segments = [c for c in candidates if c.causal_category == "segment_concentration"]

    mechanisms.sort(key=lambda x: x.score, reverse=True)
    segments.sort(key=lambda x: x.score, reverse=True)

    final_ranked = (mechanisms + segments)[:max_causes]

    # Assign sequential ranks
    for idx, item in enumerate(final_ranked, start=1):
        item.rank = idx

    return final_ranked
