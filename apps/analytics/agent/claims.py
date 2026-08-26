"""Deterministic Evidence-Backed Claim Generator for RootCause AI."""

from typing import Literal

from apps.analytics.agent.models import EvidenceBackedClaim, RankedRootCause
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)


def _to_claim_direction(
    val: str | None,
) -> Literal["increase", "decrease", "neutral", "normal"] | None:
    """Normalize direction strings into standard claim direction literals."""
    if not val:
        return None
    val_lower = val.lower()
    if val_lower in ("increase", "surge", "expansion", "up"):
        return "increase"
    elif val_lower in ("decrease", "drop", "contraction", "down"):
        return "decrease"
    elif val_lower == "normal":
        return "normal"
    return "neutral"


def generate_evidence_backed_claims(
    summary: AnomalySummary,
    decomposition: VolumeValueDecomposition | None,
    operational_signals: OperationalIndicators | None,
    contributors: list[DimensionContributor],
    top_root_causes: list[RankedRootCause],
) -> list[EvidenceBackedClaim]:
    """Deterministically synthesize verified, evidence-backed claims."""
    claims: list[EvidenceBackedClaim] = []
    anom_date = summary.anomaly_date
    anom_str = anom_date.isoformat()
    sum_dir = _to_claim_direction(summary.direction)

    # 1. Headline Anomaly Claim
    pct_str = (
        f"{summary.percentage_change:+.1f}%"
        if summary.percentage_change is not None
        else "N/A"
    )
    claims.append(
        EvidenceBackedClaim(
            evidence_id=f"ev_kpi_{summary.metric}_{anom_str}",
            claim_type="anomaly",
            subject=(
                f"{summary.metric} {summary.direction} to "
                f"{summary.observed_value:,.2f} vs {summary.baseline_value:,.2f} "
                f"baseline ({pct_str})."
            ),
            metric=summary.metric,
            value=summary.observed_value,
            baseline_value=summary.baseline_value,
            delta=summary.absolute_change,
            percentage_change=summary.percentage_change,
            direction=sum_dir,
            dimension=None,
            dimension_value=None,
            causal_mechanism=None,
            derived_formula=None,
        )
    )

    # 2. Volume & AOV Decomposition Claims
    if decomposition:
        d = decomposition
        if d.baseline_orders > 0:
            ord_pct = round(
                ((d.observed_orders - d.baseline_orders) / d.baseline_orders) * 100.0,
                2,
            )
        else:
            ord_pct = 0.0

        vol_dir: Literal["increase", "decrease"] = (
            "increase" if d.observed_orders >= d.baseline_orders else "decrease"
        )
        claims.append(
            EvidenceBackedClaim(
                evidence_id=f"ev_decomp_vol_{anom_str}",
                claim_type="numerical",
                subject=(
                    f"Order volume shifted {ord_pct:+.1f}% vs baseline "
                    f"({d.observed_orders:,.0f} vs "
                    f"{d.baseline_orders:,.0f} baseline orders)."
                ),
                metric="orders_count",
                value=ord_pct,
                baseline_value=d.baseline_orders,
                delta=d.observed_orders - d.baseline_orders,
                percentage_change=ord_pct,
                direction=vol_dir,
                dimension="order_volume",
                dimension_value="volume",
                causal_mechanism="order_volume",
                derived_formula="percentage_change",
            )
        )

        if d.volume_contribution_pct is not None:
            claims.append(
                EvidenceBackedClaim(
                    evidence_id=f"ev_decomp_vol_{anom_str}",
                    claim_type="causal",
                    subject=(
                        f"Volume change explains "
                        f"{d.volume_contribution_pct:+.1f}% of total "
                        f"GMV variance (R$ {d.volume_effect:+,.2f})."
                    ),
                    metric="orders_count",
                    value=d.volume_contribution_pct,
                    baseline_value=None,
                    delta=d.volume_effect,
                    percentage_change=d.volume_contribution_pct,
                    direction=vol_dir,
                    dimension="order_volume",
                    dimension_value="volume",
                    causal_mechanism="order_volume",
                    derived_formula="contribution_percentage",
                )
            )

        if d.baseline_aov > 0:
            aov_pct = round(
                ((d.observed_aov - d.baseline_aov) / d.baseline_aov) * 100.0, 2
            )
        else:
            aov_pct = 0.0

        aov_dir: Literal["increase", "decrease"] = (
            "increase" if d.observed_aov >= d.baseline_aov else "decrease"
        )
        claims.append(
            EvidenceBackedClaim(
                evidence_id=f"ev_decomp_aov_{anom_str}",
                claim_type="numerical",
                subject=(
                    f"Average basket size shifted {aov_pct:+.1f}% vs baseline "
                    f"(R$ {d.observed_aov:.2f} vs "
                    f"R$ {d.baseline_aov:.2f} baseline AOV)."
                ),
                metric="average_order_value",
                value=aov_pct,
                baseline_value=d.baseline_aov,
                delta=d.observed_aov - d.baseline_aov,
                percentage_change=aov_pct,
                direction=aov_dir,
                dimension="average_order_value",
                dimension_value="aov",
                causal_mechanism="average_order_value",
                derived_formula="percentage_change",
            )
        )

        if d.aov_contribution_pct is not None:
            claims.append(
                EvidenceBackedClaim(
                    evidence_id=f"ev_decomp_aov_{anom_str}",
                    claim_type="causal",
                    subject=(
                        f"Basket pricing explains "
                        f"{d.aov_contribution_pct:+.1f}% of total "
                        f"GMV variance (R$ {d.aov_effect:+,.2f})."
                    ),
                    metric="average_order_value",
                    value=d.aov_contribution_pct,
                    baseline_value=None,
                    delta=d.aov_effect,
                    percentage_change=d.aov_contribution_pct,
                    direction=aov_dir,
                    dimension="average_order_value",
                    dimension_value="aov",
                    causal_mechanism="average_order_value",
                    derived_formula="contribution_percentage",
                )
            )

    # 3. Operational & Delivery Signals Claims
    if operational_signals and (
        summary.metric in ("late_delivery_rate_pct", "delivery")
        or operational_signals.late_delivery_rate_change != 0
    ):
        op = operational_signals
        op_dir: Literal["increase", "decrease"] = (
            "increase" if op.late_delivery_rate_change >= 0 else "decrease"
        )
        claims.append(
            EvidenceBackedClaim(
                evidence_id=f"ev_ops_delivery_{anom_str}",
                claim_type="operational",
                subject=(
                    f"Late delivery rate rose to {op.observed_late_delivery_rate:.1f}% "
                    f"(vs {op.baseline_late_delivery_rate:.1f}% baseline)."
                ),
                metric="late_delivery_rate_pct",
                value=op.observed_late_delivery_rate,
                baseline_value=op.baseline_late_delivery_rate,
                delta=op.late_delivery_rate_change,
                percentage_change=None,
                direction=op_dir,
                dimension="delivery",
                dimension_value="late_delivery",
                causal_mechanism="delivery",
                derived_formula=None,
            )
        )

    # 4. Top Segment Slices Claims
    for c in contributors[:3]:
        c_dir = _to_claim_direction(c.direction)
        share_pct = c.contribution_pct or 0.0
        claims.append(
            EvidenceBackedClaim(
                evidence_id=f"ev_slice_{c.dimension}_{c.dimension_value}_{anom_str}",
                claim_type="segment",
                subject=(
                    f"Concentrated in {c.dimension_value} "
                    f"({share_pct:+.1f}% share, R$ {c.absolute_change:+,.2f})."
                ),
                metric=summary.metric,
                value=share_pct,
                baseline_value=c.baseline_value,
                delta=c.absolute_change,
                percentage_change=c.percentage_change,
                direction=c_dir,
                dimension=c.dimension,
                dimension_value=c.dimension_value,
                causal_mechanism=None,
                derived_formula="contribution_percentage",
            )
        )

    # 5. Causal Root Cause Claims
    if top_root_causes:
        primary = top_root_causes[0]
        d_code = "vol" if primary.dimension == "order_volume" else "aov"
        s_code = f"{primary.dimension}_{primary.dimension_value}_{anom_str}"
        if primary.dimension in ("order_volume", "average_order_value"):
            ev_id = f"ev_decomp_{d_code}_{anom_str}"
        elif primary.dimension == "delivery":
            ev_id = f"ev_ops_delivery_{anom_str}"
        else:
            ev_id = f"ev_slice_{s_code}"

        claims.append(
            EvidenceBackedClaim(
                evidence_id=ev_id,
                claim_type="causal",
                subject=f"Root Cause: {primary.title} (Verified mart math).",
                metric=summary.metric,
                value=None,
                baseline_value=None,
                delta=None,
                percentage_change=None,
                direction=None,
                dimension=primary.dimension,
                dimension_value=primary.dimension_value,
                causal_mechanism=primary.causal_mechanism,
                derived_formula=None,
            )
        )

    return claims
