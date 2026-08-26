"""Investigation Planner for constructing adaptive investigation plans."""

from typing import Any

from apps.analytics.agent.models import (
    InvestigationAgentRequest,
    InvestigationState,
)


def generate_initial_plan(request: InvestigationAgentRequest) -> list[str]:
    """Construct deterministic queue of investigation branches."""
    metric = request.metric
    dimensions = set(request.dimensions)

    plan: list[str] = []

    # 1. Macro decomposition for GMV
    if metric == "total_gmv":
        plan.append("volume_aov_decomposition")

    # 2. Regional analysis
    if "customer_state" in dimensions:
        plan.append("customer_state_drilldown")

    # 3. Category analysis
    if "product_category" in dimensions:
        plan.append("product_category_drilldown")

    # 4. Merchant analysis
    if "seller" in dimensions:
        plan.append("seller_drilldown")

    # 5. Operational telemetry & sentiment
    plan.append("operational_signals_evaluation")
    plan.append("customer_sentiment_evaluation")

    return plan[: request.max_investigation_steps]


def adapt_plan_with_evidence(
    state: InvestigationState,
    current_branch: str,
    evidence: dict[str, Any],
) -> None:
    """Adapt remaining pending branches based on accumulated evidence."""
    if current_branch == "volume_aov_decomposition":
        decomp = evidence.get("decomposition")
        if decomp:
            vol_pct = getattr(decomp, "volume_contribution_pct", 0.0) or 0.0
            if vol_pct > 80.0 and "customer_state_drilldown" in state.pending_steps:
                state.pending_steps.remove("customer_state_drilldown")
                state.pending_steps.insert(0, "customer_state_drilldown")
