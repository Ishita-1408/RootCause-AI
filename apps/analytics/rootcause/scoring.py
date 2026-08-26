"""Scoring and mathematical decomposition functions for Root-Cause Analysis."""

from typing import Literal

from apps.analytics.rootcause.models import (
    DimensionContributor,
    VolumeValueDecomposition,
)
from apps.analytics.rootcause.queries import SliceRecord


def calculate_slice_contributors(
    slices: list[SliceRecord],
    dimension_name: str,
    total_metric_change: float,
    max_results: int = 10,
) -> list[DimensionContributor]:
    """Calculate absolute changes, percentage shifts, and contribution percentages."""
    raw_entries: list[dict[str, float | str | None]] = []

    for s in slices:
        obs = s["observed_value"]
        base = s["baseline_value"]
        diff = round(obs - base, 2)

        pct_change: float | None = None
        if base > 0:
            pct_change = round((diff / base) * 100.0, 2)
        elif base == 0 and obs > 0:
            pct_change = 100.0
        elif base == 0 and obs == 0:
            pct_change = 0.0

        contrib_pct: float | None = None
        if total_metric_change != 0:
            contrib_pct = round((diff / abs(total_metric_change)) * 100.0, 2)

        direction: Literal["increase", "decrease", "unchanged"] = "unchanged"
        if diff > 0:
            direction = "increase"
        elif diff < 0:
            direction = "decrease"

        raw_entries.append(
            {
                "dimension": dimension_name,
                "dimension_value": s["slice_value"],
                "observed_value": obs,
                "baseline_value": base,
                "absolute_change": diff,
                "percentage_change": pct_change,
                "contribution_pct": contrib_pct,
                "direction": direction,
                "abs_diff": abs(diff),
            }
        )

    # Sort by absolute change magnitude descending
    raw_entries.sort(key=lambda x: float(x["abs_diff"]), reverse=True)  # type: ignore[arg-type]

    contributors: list[DimensionContributor] = []
    for rank_idx, item in enumerate(raw_entries[:max_results], start=1):
        contributors.append(
            DimensionContributor(
                dimension=str(item["dimension"]),
                dimension_value=str(item["dimension_value"]),
                observed_value=float(item["observed_value"]),  # type: ignore[arg-type]
                baseline_value=float(item["baseline_value"]),  # type: ignore[arg-type]
                absolute_change=float(item["absolute_change"]),  # type: ignore[arg-type]
                percentage_change=item["percentage_change"],  # type: ignore[arg-type]
                contribution_pct=item["contribution_pct"],  # type: ignore[arg-type]
                direction=item["direction"],  # type: ignore[arg-type]
                rank=rank_idx,
            )
        )

    return contributors


def decompose_volume_and_aov(
    observed_orders: float,
    baseline_orders: float,
    observed_aov: float,
    baseline_aov: float,
) -> VolumeValueDecomposition:
    """Decompose revenue change into Volume, AOV, and Interaction components.

    Mathematical Formulation:
        GMV = Orders * AOV
        Delta Orders = observed_orders - baseline_orders
        Delta AOV = observed_aov - baseline_aov

        Volume Effect = Delta Orders * baseline_aov
        AOV Effect = Delta AOV * baseline_orders
        Interaction Effect = Delta Orders * Delta AOV
        Total Change = Volume Effect + AOV Effect + Interaction Effect
    """
    delta_orders = round(observed_orders - baseline_orders, 4)
    delta_aov = round(observed_aov - baseline_aov, 4)

    vol_effect = round(delta_orders * baseline_aov, 2)
    aov_effect = round(delta_aov * baseline_orders, 2)
    inter_effect = round(delta_orders * delta_aov, 2)

    total_change = round(vol_effect + aov_effect + inter_effect, 2)

    vol_contrib_pct = (
        round((vol_effect / abs(total_change)) * 100.0, 2)
        if total_change != 0
        else None
    )
    aov_contrib_pct = (
        round((aov_effect / abs(total_change)) * 100.0, 2)
        if total_change != 0
        else None
    )
    inter_contrib_pct = (
        round((inter_effect / abs(total_change)) * 100.0, 2)
        if total_change != 0
        else None
    )

    return VolumeValueDecomposition(
        observed_orders=round(observed_orders, 2),
        baseline_orders=round(baseline_orders, 2),
        observed_aov=round(observed_aov, 2),
        baseline_aov=round(baseline_aov, 2),
        volume_effect=vol_effect,
        aov_effect=aov_effect,
        interaction_effect=inter_effect,
        total_change=total_change,
        volume_contribution_pct=vol_contrib_pct,
        aov_contribution_pct=aov_contrib_pct,
        interaction_contribution_pct=inter_contrib_pct,
    )
