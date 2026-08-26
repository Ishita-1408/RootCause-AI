"""Extractors for transforming responses into Claims and Evidence."""

import re
from typing import Literal

from apps.analytics.agent.models import InvestigationAgentResponse
from evaluation.hallucination.models import (
    ClaimType,
    EvidenceRecord,
    StructuredClaim,
)


def _to_claim_direction(
    val: str | None,
) -> Literal["increase", "decrease", "neutral", "normal"] | None:
    """Normalize direction strings into approved literals."""
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


def extract_evidence_from_response(
    response: InvestigationAgentResponse,
) -> list[EvidenceRecord]:
    """Extract a complete pool of empirical evidence records from an agent response."""
    evidence_pool: list[EvidenceRecord] = []
    summary = response.anomaly_summary
    anom_date = summary.anomaly_date
    comp_days = (summary.baseline_end_date - summary.baseline_start_date).days + 1
    sum_dir = _to_claim_direction(summary.direction) or "neutral"

    # 1. Main KPI Anomaly Evidence
    evidence_pool.append(
        EvidenceRecord(
            evidence_id=f"ev_kpi_{summary.metric}_{anom_date.isoformat()}",
            source="mart_daily_kpis",
            metric=summary.metric,
            observed_value=summary.observed_value,
            baseline_value=summary.baseline_value,
            delta=summary.absolute_change,
            delta_pct=summary.percentage_change,
            direction=sum_dir,
            dimension=None,
            dimension_value=None,
            anomaly_date=anom_date,
            comparison_window=comp_days,
            query_tool_id="fetch_date_metrics",
            raw_details={
                "metric": summary.metric,
                "observed_value": summary.observed_value,
                "baseline_value": summary.baseline_value,
            },
        )
    )

    # 2. Volume & AOV Decomposition Evidence
    if response.decomposition:
        d = response.decomposition
        vol_pct = d.volume_contribution_pct or 0.0
        aov_pct = d.aov_contribution_pct or 0.0
        dominant = (
            "order_volume" if abs(vol_pct) >= abs(aov_pct) else "average_order_value"
        )

        evidence_pool.append(
            EvidenceRecord(
                evidence_id=f"ev_decomp_vol_{anom_date.isoformat()}",
                source="decomposition_engine",
                metric="orders_count",
                observed_value=d.observed_orders,
                baseline_value=d.baseline_orders,
                delta=d.observed_orders - d.baseline_orders,
                delta_pct=vol_pct,
                direction="increase" if vol_pct >= 0 else "decrease",
                dimension="order_volume",
                dimension_value="volume",
                anomaly_date=anom_date,
                comparison_window=comp_days,
                query_tool_id="decompose_volume_and_aov",
                raw_details={
                    "volume_effect": d.volume_effect,
                    "volume_contribution_pct": d.volume_contribution_pct,
                    "dominant_mechanism": dominant,
                },
            )
        )

        evidence_pool.append(
            EvidenceRecord(
                evidence_id=f"ev_decomp_aov_{anom_date.isoformat()}",
                source="decomposition_engine",
                metric="average_order_value",
                observed_value=d.observed_aov,
                baseline_value=d.baseline_aov,
                delta=d.observed_aov - d.baseline_aov,
                delta_pct=aov_pct,
                direction="increase" if aov_pct >= 0 else "decrease",
                dimension="average_order_value",
                dimension_value="aov",
                anomaly_date=anom_date,
                comparison_window=comp_days,
                query_tool_id="decompose_volume_and_aov",
                raw_details={
                    "aov_effect": d.aov_effect,
                    "aov_contribution_pct": d.aov_contribution_pct,
                    "dominant_mechanism": dominant,
                },
            )
        )

    # 3. Dimensional Slice Contributors
    slice_metric = (
        summary.metric if summary.metric != "late_delivery_rate_pct" else "total_gmv"
    )
    for c in response.supporting_evidence:
        c_dir = _to_claim_direction(c.direction) or "neutral"
        evidence_pool.append(
            EvidenceRecord(
                evidence_id=f"ev_slice_{c.dimension}_{c.dimension_value}_{anom_date.isoformat()}",
                source="contribution_analyzer",
                metric=slice_metric,
                observed_value=c.observed_value,
                baseline_value=c.baseline_value,
                delta=c.absolute_change,
                delta_pct=c.percentage_change,
                direction=c_dir,
                dimension=c.dimension,
                dimension_value=c.dimension_value,
                anomaly_date=anom_date,
                comparison_window=comp_days,
                query_tool_id="analyze_dimension_breakdown",
                raw_details={
                    "contribution_pct": c.contribution_pct,
                    "rank": c.rank,
                },
            )
        )

    # 4. Operational Indicators
    ops = response.operational_signals
    evidence_pool.append(
        EvidenceRecord(
            evidence_id=f"ev_ops_delivery_{anom_date.isoformat()}",
            source="operational_indicators",
            metric="late_delivery_rate_pct",
            observed_value=ops.observed_late_delivery_rate,
            baseline_value=ops.baseline_late_delivery_rate,
            delta=ops.late_delivery_rate_change,
            delta_pct=None,
            direction="increase" if ops.late_delivery_rate_change > 0 else "decrease",
            dimension="delivery",
            dimension_value="late_delivery",
            anomaly_date=anom_date,
            comparison_window=comp_days,
            query_tool_id="fetch_operational_indicators",
            raw_details={
                "delivery_days_change": ops.avg_delivery_days_change,
                "cancellation_rate_change": ops.cancellation_rate_change,
            },
        )
    )

    return evidence_pool


def extract_claims_from_response(
    response: InvestigationAgentResponse,
) -> list[StructuredClaim]:
    """Extract structured claims from ranked causes, decomposition, and findings."""
    claims: list[StructuredClaim] = []
    summary = response.anomaly_summary
    anom_date = summary.anomaly_date
    comp_days = (summary.baseline_end_date - summary.baseline_start_date).days + 1
    sum_dir = _to_claim_direction(summary.direction)

    # 1. Claim from Macro Anomaly Summary
    claims.append(
        StructuredClaim(
            claim_id=f"clm_kpi_summary_{anom_date.isoformat()}",
            claim_type="anomaly",
            metric=summary.metric,
            subject=f"{summary.metric} {summary.direction} on {anom_date}",
            value=summary.observed_value,
            unit="BRL"
            if "gmv" in summary.metric or "value" in summary.metric
            else "count",
            direction=sum_dir,
            dimension=None,
            dimension_value=None,
            anomaly_date=anom_date,
            comparison_window=comp_days,
            evidence_ids=[f"ev_kpi_{summary.metric}_{anom_date.isoformat()}"],
            causal_mechanism=None,
            derived_formula=None,
        )
    )

    # 2. Claims from Ranked Root Causes
    for rc in response.top_root_causes:
        c_type: ClaimType = (
            "causal"
            if rc.causal_category in ("macro_driver", "operational_mechanism")
            else "segment"
        )
        formula: str | None = (
            "contribution_percentage"
            if rc.contribution_pct is not None
            else "absolute_change"
        )

        d_tag = "vol" if rc.dimension == "order_volume" else "aov"
        s_suf = f"{rc.dimension}_{rc.dimension_value}_{anom_date.isoformat()}"

        if rc.dimension in ("order_volume", "average_order_value"):
            ev_id = f"ev_decomp_{d_tag}_{anom_date.isoformat()}"
            rc_metric = (
                "orders_count"
                if rc.dimension == "order_volume"
                else "average_order_value"
            )
        elif rc.dimension == "delivery":
            ev_id = f"ev_ops_delivery_{anom_date.isoformat()}"
            rc_metric = "late_delivery_rate_pct"
        else:
            ev_id = f"ev_slice_{s_suf}"
            rc_metric = (
                summary.metric
                if summary.metric != "late_delivery_rate_pct"
                else "total_gmv"
            )

        claims.append(
            StructuredClaim(
                claim_id=(
                    f"clm_rc_rank_{rc.rank}_{rc.dimension}_"
                    f"{rc.dimension_value or 'all'}"
                ),
                claim_type=c_type,
                metric=rc_metric,
                subject=f"Rank #{rc.rank}: {rc.title}",
                value=rc.contribution_pct,
                unit="pct",
                direction="increase" if rc.absolute_change >= 0 else "decrease",
                dimension=rc.dimension,
                dimension_value=rc.dimension_value,
                anomaly_date=anom_date,
                comparison_window=comp_days,
                evidence_ids=[ev_id],
                causal_mechanism=rc.causal_mechanism,
                derived_formula=formula,
            )
        )

    # 3. Claims parsed from key findings
    for idx, finding in enumerate(response.key_findings, 1):
        f_lower = finding.lower()
        pct_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%", finding)
        val = float(pct_match.group(1)) if pct_match else None
        dir_val = _to_claim_direction(
            "increase"
            if any(
                w in f_lower
                for w in ["increase", "grew", "surge", "expansion", "up", "gained"]
            )
            else "decrease"
            if any(
                w in f_lower
                for w in ["decrease", "drop", "contraction", "down", "fell", "loss"]
            )
            else None
        )

        # Subject metric inference
        if "order" in f_lower or "volume" in f_lower:
            subj_metric = "orders_count"
            dim = "order_volume"
            dim_val = "volume"
        elif (
            "aov" in f_lower or "average order value" in f_lower or "basket" in f_lower
        ):
            subj_metric = "average_order_value"
            dim = "average_order_value"
            dim_val = "aov"
        elif any(
            w in f_lower for w in ["delivery", "carrier", "transit", "sla", "delay"]
        ):
            subj_metric = "late_delivery_rate_pct"
            dim = "delivery"
            dim_val = "late_delivery"
        else:
            subj_metric = summary.metric
            dim = None
            dim_val = None

        # Check for segment matches with word boundary check
        # (e.g. avoids matching 'ba' in 'baseline')
        for cand_dim in ["customer_state", "product_category", "seller"]:
            for slice_ev in response.supporting_evidence:
                dim_str = str(slice_ev.dimension_value).lower()
                pattern = r"\b" + re.escape(dim_str) + r"\b"
                if slice_ev.dimension == cand_dim and re.search(pattern, f_lower):
                    dim = cand_dim
                    dim_val = slice_ev.dimension_value
                    subj_metric = (
                        summary.metric
                        if summary.metric != "late_delivery_rate_pct"
                        else "total_gmv"
                    )
                    break

        # Formula and value type inference
        f_formula: str | None = None
        if any(w in f_lower for w in ["share", "explains", "contribut", "variance"]):
            f_formula = "contribution_percentage"
        elif any(w in f_lower for w in ["shifted", "grew", "dropped", "(+", "(-"]):
            f_formula = "percentage_change"
        elif "rose to" in f_lower or "fell to" in f_lower:
            if "late_delivery" in f_lower or "rate" in f_lower:
                f_formula = None
            else:
                f_formula = "percentage_change" if pct_match else None
        elif pct_match:
            f_formula = "percentage_change"

        claims.append(
            StructuredClaim(
                claim_id=f"clm_finding_{idx}",
                claim_type="numerical" if val is not None else "trend",
                metric=subj_metric,
                subject=finding,
                value=val,
                unit="pct" if pct_match else None,
                direction=dir_val,
                dimension=dim,
                dimension_value=dim_val,
                anomaly_date=anom_date,
                comparison_window=comp_days,
                evidence_ids=[],
                causal_mechanism=None,
                derived_formula=f_formula,
            )
        )

    return claims
