"""AI Investigation Service for generating executive business reports."""

import json
import logging
from typing import Any

from apps.ai.models import (
    AIInvestigationEvidence,
    AIInvestigationResponse,
)
from apps.ai.prompts import SYSTEM_PROMPT, build_investigation_prompt
from apps.ai.provider import (
    DeterministicFallbackProvider,
    LLMProvider,
    get_default_provider,
)
from apps.analytics.rootcause.models import RootCauseInvestigationResponse

logger = logging.getLogger(__name__)


def extract_evidence_payload(
    resp: RootCauseInvestigationResponse,
) -> AIInvestigationEvidence:
    """Deterministically convert response into compact evidence."""
    top_contribs: list[dict[str, Any]] = []
    for c in resp.ranked_contributors:
        top_contribs.append(
            {
                "dimension": c.dimension,
                "dimension_value": c.dimension_value,
                "observed_value": c.observed_value,
                "baseline_value": c.baseline_value,
                "absolute_change": c.absolute_change,
                "percentage_change": c.percentage_change,
                "contribution_pct": c.contribution_pct,
                "direction": c.direction,
                "rank": c.rank,
            }
        )

    orders_obs = None
    orders_base = None
    orders_pct = None
    aov_obs = None
    aov_base = None
    aov_pct = None
    vol_eff = None
    aov_eff = None
    inter_eff = None

    if resp.decomposition:
        orders_obs = resp.decomposition.observed_orders
        orders_base = resp.decomposition.baseline_orders
        if orders_base > 0:
            orders_pct = round(((orders_obs - orders_base) / orders_base) * 100.0, 2)
        aov_obs = resp.decomposition.observed_aov
        aov_base = resp.decomposition.baseline_aov
        if aov_base > 0:
            aov_pct = round(((aov_obs - aov_base) / aov_base) * 100.0, 2)
        vol_eff = resp.decomposition.volume_effect
        aov_eff = resp.decomposition.aov_effect
        inter_eff = resp.decomposition.interaction_effect

    op = resp.operational_indicators
    op_indicators = {
        "observed_late_delivery_rate": op.observed_late_delivery_rate,
        "baseline_late_delivery_rate": op.baseline_late_delivery_rate,
        "late_delivery_rate_change": op.late_delivery_rate_change,
        "observed_avg_delivery_days": op.observed_avg_delivery_days,
        "baseline_avg_delivery_days": op.baseline_avg_delivery_days,
        "observed_avg_review_score": op.observed_avg_review_score,
        "baseline_avg_review_score": op.baseline_avg_review_score,
    }

    base_period_str = (
        f"{resp.summary.baseline_start_date} to {resp.summary.baseline_end_date}"
    )

    return AIInvestigationEvidence(
        metric=resp.summary.metric,
        anomaly_date=resp.summary.anomaly_date.isoformat(),
        baseline_period=base_period_str,
        observed_value=resp.summary.observed_value,
        baseline_value=resp.summary.baseline_value,
        absolute_change=resp.summary.absolute_change,
        percentage_change=resp.summary.percentage_change,
        direction=resp.summary.direction,
        orders_observed=orders_obs,
        orders_baseline=orders_base,
        orders_change_pct=orders_pct,
        aov_observed=aov_obs,
        aov_baseline=aov_base,
        aov_change_pct=aov_pct,
        volume_effect=vol_eff,
        aov_effect=aov_eff,
        interaction_effect=inter_eff,
        top_contributors=top_contribs,
        operational_indicators=op_indicators,
        deterministic_summary=resp.explanation,
        limitations=resp.limitations,
    )


def investigate_with_ai(
    root_cause_response: RootCauseInvestigationResponse,
    provider: LLMProvider | None = None,
) -> AIInvestigationResponse:
    """Synthesize validated root-cause evidence into an executive AI summary."""
    active_provider = provider or get_default_provider()
    evidence = extract_evidence_payload(root_cause_response)
    prompt = build_investigation_prompt(evidence)

    model_name = getattr(active_provider, "model", "deterministic-fallback")
    is_fallback = isinstance(active_provider, DeterministicFallbackProvider)

    try:
        raw_response = active_provider.generate(
            prompt=prompt, system_prompt=SYSTEM_PROMPT
        )
        cleaned = raw_response.strip().removeprefix("```json").removesuffix("```")
        parsed = json.loads(cleaned)

        return AIInvestigationResponse(
            investigation_title=str(
                parsed.get("investigation_title", "Root-Cause Investigation")
            ),
            executive_summary=str(parsed.get("executive_summary", "")),
            key_findings=[str(x) for x in parsed.get("key_findings", [])],
            business_interpretation=[
                str(x) for x in parsed.get("business_interpretation", [])
            ],
            recommended_actions=[str(x) for x in parsed.get("recommended_actions", [])],
            limitations=[str(x) for x in parsed.get("limitations", [])],
            model=model_name,
            is_fallback=is_fallback,
        )
    except Exception as e:
        logger.warning(
            f"LLM generation or parsing failed ({e}). Falling back to synthesizer."
        )
        fallback = DeterministicFallbackProvider()
        fallback_json = json.loads(fallback.generate(prompt=prompt))
        return AIInvestigationResponse(
            investigation_title=str(
                fallback_json.get("investigation_title", "Root-Cause Investigation")
            ),
            executive_summary=str(fallback_json.get("executive_summary", "")),
            key_findings=[str(x) for x in fallback_json.get("key_findings", [])],
            business_interpretation=[
                str(x) for x in fallback_json.get("business_interpretation", [])
            ],
            recommended_actions=[
                str(x) for x in fallback_json.get("recommended_actions", [])
            ],
            limitations=[str(x) for x in fallback_json.get("limitations", [])],
            model="deterministic-rule-synthesizer",
            is_fallback=True,
        )
