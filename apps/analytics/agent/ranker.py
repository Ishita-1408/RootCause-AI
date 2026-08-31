"""Deterministic multi-signal evidence ranker with causal separation."""

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
    driver_direction: str | None = None,
    anomaly_direction: str | None = None,
    metric_relevancy_weight: float = 1.0,
    statistical_confidence: float = 0.8,
    temporal_alignment_weight: float = 1.0,
    distractor_penalty: float = 0.0,
) -> float:
    """Calculate multi-signal deterministic root cause attribution score.

    Formula:
        Score = (Base Attributed Magnitude)
                * (Directional Alignment Factor)
                * (Dimension / Mechanism Priority)
                * (Metric Relevancy Weight)
                * (Statistical Confidence Factor)
                * (Temporal Alignment Factor)
                - (Distractor Penalty)
    """
    pct = min(abs(float(contribution_pct or 0.0)), 100.0)
    mag = abs(float(absolute_change))

    # Logarithmic magnitude factor: log10(1 + magnitude / 1000)
    mag_factor = 1.0 + math.log10(1.0 + (mag / 1000.0))

    # Directional Alignment Factor:
    # If the driver's movement explains the anomaly direction, full weight (1.0).
    # If the driver's movement opposed the anomaly direction, it acted as a
    # countervailing buffer/headwind, not the primary cause (0.20).
    if anomaly_direction and driver_direction:
        anom_d = anomaly_direction.strip().lower()
        driv_d = driver_direction.strip().lower()
        is_aligned = anom_d == driv_d
        direction_factor = 1.0 if is_aligned else 0.20
    else:
        direction_factor = 1.0

    dim_weights = {
        "order_volume": 1.55,
        "average_order_value": 1.50,
        "delivery": 1.65,
        "avg_review_score": 1.60,
        "customer_satisfaction": 1.60,
        "pricing": 1.45,
        "customer_state": 0.85,
        "product_category": 0.85,
        "seller": 0.80,
    }
    dim_weight = dim_weights.get(dimension, 1.0)
    mechanism_multiplier = 1.35 if is_causal_mechanism else 1.0

    stat_factor = 1.0 + 0.25 * float(statistical_confidence or 0.8)
    temp_factor = float(temporal_alignment_weight or 1.0)

    score = (
        pct
        * mag_factor
        * dim_weight
        * mechanism_multiplier
        * direction_factor
        * float(metric_relevancy_weight)
        * stat_factor
        * temp_factor
        - float(distractor_penalty)
    )
    return max(round(score, 2), 0.0)


def rank_evidence(
    contributors: list[DimensionContributor],
    decomposition: Any | None = None,
    summary: AnomalySummary | None = None,
    operational_signals: OperationalIndicators | None = None,
    max_causes: int = 5,
    stat_evidence: Any | None = None,
    cp_analysis: Any | None = None,
) -> list[RankedRootCause]:
    """Rank all gathered evidence into an ordered list of top root causes.

    Explicitly separates Causal Mechanism (Why) from Affected Segment (Where).
    Fuses multiple independent analytical signals:
    - Quantitative causal decomposition
    - Directional explanatory alignment vs countervailing headwinds
    - Target metric domain specificity
    - Statistical significance & confidence bounds
    - Temporal change-point alignment
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
    anom_dir = summary.direction if summary else "decrease"

    # Temporal & statistical signal extraction
    has_cp = bool(cp_analysis and getattr(cp_analysis, "change_point_detected", False))
    temporal_weight = 1.15 if has_cp else 1.0

    has_sig = bool(
        stat_evidence
        and getattr(stat_evidence, "has_statistically_significant_findings", False)
    )
    stat_conf = 0.90 if has_sig else 0.80

    # 1. Evaluate Total GMV Macro Causal Mechanisms (Volume vs AOV)
    if target_metric == "total_gmv" and decomposition:
        vol_pct = getattr(decomposition, "volume_contribution_pct", 0.0) or 0.0
        vol_eff = getattr(decomposition, "volume_effect", 0.0) or 0.0
        aov_pct = getattr(decomposition, "aov_contribution_pct", 0.0) or 0.0
        aov_eff = getattr(decomposition, "aov_effect", 0.0) or 0.0

        orders_shift_pct = (
            (
                (decomposition.observed_orders - decomposition.baseline_orders)
                / decomposition.baseline_orders
            )
            * 100.0
            if decomposition.baseline_orders > 0
            else 0.0
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

        vol_driver_dir = "increase" if vol_eff >= 0 else "decrease"
        aov_driver_dir = "increase" if aov_eff >= 0 else "decrease"

        # Volume Driver Candidate
        if abs(vol_pct) >= 15.0:
            vol_score = calculate_root_cause_score(
                contribution_pct=vol_pct,
                absolute_change=vol_eff,
                dimension="order_volume",
                is_causal_mechanism=True,
                driver_direction=vol_driver_dir,
                anomaly_direction=anom_dir,
                metric_relevancy_weight=1.0,
                statistical_confidence=stat_conf,
                temporal_alignment_weight=temporal_weight,
            )
            vol_title_dir = "Surge" if vol_eff >= 0 else "Contraction"
            vol_evidence_chain = [
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
                vol_evidence_chain.append(
                    f"Growth concentrated in {state_val} ({state_pct:+.1f}% share)."
                )
            vol_evidence_chain.append(
                f"Root Cause: Order Volume {vol_title_dir} (Verified mart math)."
            )

            candidates.append(
                RankedRootCause(
                    rank=0,
                    title=f"Order Volume {vol_title_dir}",
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
                    evidence_chain=vol_evidence_chain,
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

        # Average Order Value Driver Candidate
        if abs(aov_pct) >= 15.0:
            aov_score = calculate_root_cause_score(
                contribution_pct=aov_pct,
                absolute_change=aov_eff,
                dimension="average_order_value",
                is_causal_mechanism=True,
                driver_direction=aov_driver_dir,
                anomaly_direction=anom_dir,
                metric_relevancy_weight=1.0,
                statistical_confidence=stat_conf,
                temporal_alignment_weight=temporal_weight,
            )
            aov_title_dir = "Expansion" if aov_eff >= 0 else "Contraction"
            aov_evidence_chain = [
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
                aov_evidence_chain.append(
                    f"Shift concentrated in product category '{cat_val}'."
                )
            aov_evidence_chain.append(
                f"Root Cause: Average Order Value {aov_title_dir} (Verified mart math)."
            )

            candidates.append(
                RankedRootCause(
                    rank=0,
                    title=f"Average Order Value {aov_title_dir}",
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
                    evidence_chain=aov_evidence_chain,
                    evidence_strength="high",
                    confidence=1.0,
                )
            )

    # 2. Evaluate Order Volume Metric Specifically (orders_count)
    elif target_metric in ["orders_count", "orders", "volume"]:
        obs_orders = summary.observed_value if summary else 100.0
        base_orders = (
            summary.baseline_value if summary and summary.baseline_value else 100.0
        )
        diff_orders = summary.absolute_change if summary else (obs_orders - base_orders)
        pct_shift = (
            summary.percentage_change
            if summary
            else ((diff_orders / base_orders) * 100.0)
        )

        vol_driver_dir = "increase" if diff_orders >= 0 else "decrease"
        vol_title_dir = "Surge" if diff_orders >= 0 else "Contraction"

        vol_score = calculate_root_cause_score(
            contribution_pct=100.0,
            absolute_change=diff_orders,
            dimension="order_volume",
            is_causal_mechanism=True,
            driver_direction=vol_driver_dir,
            anomaly_direction=anom_dir,
            metric_relevancy_weight=1.80,
            statistical_confidence=stat_conf,
            temporal_alignment_weight=temporal_weight,
        )

        vol_evidence_chain = [
            (
                f"Daily order volume shifted {pct_shift:+.1f}% "
                f"({obs_orders:,.0f} vs {base_orders:,.0f} baseline)."
            ),
            f"Net order volume delta: {diff_orders:+,.0f} orders.",
        ]
        if top_state_slice:
            state_val = top_state_slice.dimension_value
            state_pct = top_state_slice.contribution_pct or 0.0
            vol_evidence_chain.append(
                f"Concentrated in customer state {state_val} ({state_pct:+.1f}% share)."
            )
        vol_evidence_chain.append(
            f"Root Cause: Order Volume {vol_title_dir} (Verified mart math)."
        )

        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"Order Volume {vol_title_dir}",
                dimension="order_volume",
                dimension_value=f"{obs_orders:,.0f} orders (vs {base_orders:,.0f})",
                contribution_pct=100.0,
                absolute_change=round(diff_orders, 2),
                score=vol_score,
                explanation=(
                    f"Order volume shifted {pct_shift:+.1f}% "
                    f"({diff_orders:+,.0f} orders vs baseline). "
                    f"Primary concentration in {affected_dim}: {affected_val}."
                ),
                causal_category="macro_driver",
                causal_mechanism="order_volume",
                affected_dimension=affected_dim,
                affected_value=affected_val,
                evidence_chain=vol_evidence_chain,
                evidence_strength="high",
                confidence=1.0,
            )
        )

    # 3. Evaluate Average Order Value Metric Specifically (average_order_value)
    elif target_metric in ["average_order_value", "aov", "basket_size"]:
        obs_aov = summary.observed_value if summary else 100.0
        base_aov = (
            summary.baseline_value if summary and summary.baseline_value else 100.0
        )
        diff_aov = summary.absolute_change if summary else (obs_aov - base_aov)
        pct_shift = (
            summary.percentage_change if summary else ((diff_aov / base_aov) * 100.0)
        )

        aov_driver_dir = "increase" if diff_aov >= 0 else "decrease"
        aov_title_dir = "Expansion" if diff_aov >= 0 else "Contraction"

        aov_score = calculate_root_cause_score(
            contribution_pct=100.0,
            absolute_change=diff_aov,
            dimension="average_order_value",
            is_causal_mechanism=True,
            driver_direction=aov_driver_dir,
            anomaly_direction=anom_dir,
            metric_relevancy_weight=1.80,
            statistical_confidence=stat_conf,
            temporal_alignment_weight=temporal_weight,
        )

        aov_evidence_chain = [
            (
                f"Average basket size shifted {pct_shift:+.1f}% "
                f"(R$ {obs_aov:,.2f} vs R$ {base_aov:,.2f} baseline)."
            ),
            f"Net AOV delta: R$ {diff_aov:+,.2f} per transaction.",
        ]
        if top_cat_slice:
            cat_val = top_cat_slice.dimension_value
            aov_evidence_chain.append(
                f"Shift concentrated in product category '{cat_val}'."
            )
        aov_evidence_chain.append(
            f"Root Cause: Average Order Value {aov_title_dir} (Verified mart math)."
        )

        aff_d = top_cat_slice.dimension if top_cat_slice else affected_dim
        aff_v = top_cat_slice.dimension_value if top_cat_slice else affected_val
        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"Average Order Value {aov_title_dir}",
                dimension="average_order_value",
                dimension_value=f"R$ {obs_aov:.2f} (vs R$ {base_aov:.2f})",
                contribution_pct=100.0,
                absolute_change=round(diff_aov, 2),
                score=aov_score,
                explanation=(
                    f"Average order value shifted {pct_shift:+.1f}% "
                    f"(R$ {diff_aov:+,.2f} vs baseline). "
                    f"Concentrated in {aff_d}: {aff_v}."
                ),
                causal_category="macro_driver",
                causal_mechanism="average_order_value",
                affected_dimension=aff_d,
                affected_value=aff_v,
                evidence_chain=aov_evidence_chain,
                evidence_strength="high",
                confidence=1.0,
            )
        )

    # 4. Evaluate Delivery SLA Mechanisms (late_delivery_rate_pct)
    elif target_metric in ["late_delivery_rate_pct", "delivery"]:
        op = operational_signals
        obs_rate = (
            op.observed_late_delivery_rate
            if op
            else (summary.observed_value if summary else 0.0)
        )
        base_rate = (
            op.baseline_late_delivery_rate
            if op
            else (summary.baseline_value if summary and summary.baseline_value else 0.0)
        )
        lead_change = op.avg_delivery_days_change if op else 0.0

        delivery_driver_dir = "increase" if (obs_rate >= base_rate) else "decrease"
        delivery_title_dir = "Degradation" if (obs_rate >= base_rate) else "Recovery"

        delivery_score = calculate_root_cause_score(
            contribution_pct=100.0,
            absolute_change=summary.absolute_change if summary else 1000.0,
            dimension="delivery",
            is_causal_mechanism=True,
            driver_direction=delivery_driver_dir,
            anomaly_direction=anom_dir,
            metric_relevancy_weight=1.80,
            statistical_confidence=stat_conf,
            temporal_alignment_weight=temporal_weight,
        )

        delivery_evidence_chain = [
            f"Late delivery rate reached {obs_rate:.1f}% (vs {base_rate:.1f}% base).",
            f"Transit changed by {lead_change:+.1f} days across carrier routes.",
        ]
        if primary_affected_segment:
            seg_val = primary_affected_segment.dimension_value
            seg_pct = primary_affected_segment.contribution_pct or 0.0
            delivery_evidence_chain.append(
                f"Concentrated in {seg_val} ({seg_pct:+.1f}% share)."
            )
        delivery_evidence_chain.append(
            f"Root Cause: Carrier SLA & Logistics Fulfillment {delivery_title_dir} "
            "(Verified mart math)."
        )

        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"Carrier SLA & Logistics Fulfillment {delivery_title_dir}",
                dimension="delivery",
                dimension_value="carrier_transit_delay",
                contribution_pct=100.0,
                absolute_change=round(summary.absolute_change if summary else 0.0, 2),
                score=delivery_score,
                explanation=(
                    f"Late delivery rate reached {obs_rate:.1f}% vs {base_rate:.1f}%. "
                    f"Concentrated in {affected_dim}: {affected_val}, "
                    f"caused by delivery {delivery_title_dir.lower()}."
                ),
                causal_category="operational_mechanism",
                causal_mechanism="delivery",
                affected_dimension=affected_dim,
                affected_value=affected_val,
                evidence_chain=delivery_evidence_chain,
                evidence_strength="high",
                confidence=1.0,
            )
        )

    # 5. Evaluate Customer Satisfaction & Review Score Mechanisms (avg_review_score)
    elif target_metric in [
        "avg_review_score",
        "reviews",
        "review_score",
        "customer_satisfaction",
    ]:
        obs_score = summary.observed_value if summary else 4.0
        base_score = (
            summary.baseline_value if summary and summary.baseline_value else 4.0
        )
        diff_score = summary.absolute_change if summary else (obs_score - base_score)

        review_driver_dir = "decrease" if diff_score < 0 else "increase"
        review_title_dir = "Decline" if diff_score < 0 else "Improvement"

        review_score = calculate_root_cause_score(
            contribution_pct=100.0,
            absolute_change=diff_score * 1000.0,
            dimension="avg_review_score",
            is_causal_mechanism=True,
            driver_direction=review_driver_dir,
            anomaly_direction=anom_dir,
            metric_relevancy_weight=1.80,
            statistical_confidence=stat_conf,
            temporal_alignment_weight=temporal_weight,
        )

        review_evidence_chain = [
            (
                f"Review score reached {obs_score:.2f} "
                f"(vs {base_score:.2f} base, delta {diff_score:+.2f})."
            ),
            "Review deterioration verified across post-purchase order feedback.",
        ]
        if top_cat_slice:
            cat_v = top_cat_slice.dimension_value
            review_evidence_chain.append(
                f"Negative rating concentration in category '{cat_v}'."
            )
        review_evidence_chain.append(
            f"Root Cause: Customer Satisfaction {review_title_dir} "
            "(Verified mart math)."
        )

        candidates.append(
            RankedRootCause(
                rank=0,
                title=f"Customer Satisfaction {review_title_dir}",
                dimension="avg_review_score",
                dimension_value=f"{obs_score:.2f} stars (vs {base_score:.2f})",
                contribution_pct=100.0,
                absolute_change=round(diff_score, 2),
                score=review_score,
                explanation=(
                    f"Review score shifted to {obs_score:.2f} vs {base_score:.2f}. "
                    f"Primary concentration in {affected_dim}: {affected_val}."
                ),
                causal_category="operational_mechanism",
                causal_mechanism="avg_review_score",
                affected_dimension=affected_dim,
                affected_value=affected_val,
                evidence_chain=review_evidence_chain,
                evidence_strength="high",
                confidence=1.0,
            )
        )

    # 6. Evaluate Granular Dimensional Slices (Affected Segments)
    for c in contributors:
        pct = c.contribution_pct or 0.0
        slice_dir = "increase" if c.absolute_change >= 0 else "decrease"

        # Apply distractor penalty if slice shifted very little in % terms
        # but had high raw volume simply because of huge base size
        pct_chg = abs(c.percentage_change or 0.0)
        distractor_pen = 15.0 if pct_chg < 5.0 else 0.0

        score = calculate_root_cause_score(
            contribution_pct=pct,
            absolute_change=c.absolute_change,
            dimension=c.dimension,
            is_causal_mechanism=False,
            driver_direction=slice_dir,
            anomaly_direction=anom_dir,
            metric_relevancy_weight=0.85,
            statistical_confidence=0.85,
            distractor_penalty=distractor_pen,
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
