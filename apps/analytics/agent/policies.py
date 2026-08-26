"""Deterministic stopping policies and branching logic for Agent."""

from typing import Any

from apps.analytics.agent.models import InvestigationState


def should_terminate(state: InvestigationState) -> tuple[bool, str | None]:
    """Evaluate stopping conditions against current investigation state."""
    if state.current_step >= state.max_steps:
        return (
            True,
            f"Investigation limit ({state.max_steps} steps) reached.",
        )

    if not state.pending_steps:
        return (
            True,
            "Investigation completed: All scheduled branches evaluated.",
        )

    return False, None


def should_skip_branch(
    branch_type: str,
    evidence: dict[str, Any],
    minimum_contribution_pct: float = 5.0,
) -> tuple[bool, str | None]:
    """Check whether a planned branch should be skipped."""
    # 1. Operational branch check
    if branch_type == "operational_signals_evaluation":
        op = evidence.get("operational_indicators")
        if op:
            late_delta = getattr(op, "late_delivery_rate_change", 0.0)
            days_delta = getattr(op, "avg_delivery_days_change", 0.0)
            if abs(late_delta) < 1.0 and abs(days_delta) < 1.0:
                return (
                    True,
                    (
                        f"Operational signals stable (late Δ={late_delta:+.1f}%, "
                        f"days Δ={days_delta:+.1f}d)."
                    ),
                )

    # 2. Sentiment branch check
    if branch_type == "customer_sentiment_evaluation":
        op = evidence.get("operational_indicators")
        if op:
            score_delta = getattr(op, "avg_review_score_change", 0.0)
            if abs(score_delta) < 0.10:
                return (
                    True,
                    f"Review score stable (Δ={score_delta:+.2f} points).",
                )

    # 3. Dimensional slice check (e.g. seller)
    if branch_type == "seller_drilldown":
        sellers = evidence.get("seller_contributors", [])
        if sellers:
            top_seller_pct = getattr(sellers[0], "contribution_pct", 0.0) or 0.0
            if abs(top_seller_pct) < minimum_contribution_pct:
                return (
                    True,
                    (
                        f"Top seller ({top_seller_pct:+.1f}%) below "
                        f"threshold ({minimum_contribution_pct:.1f}%)."
                    ),
                )

    return False, None
