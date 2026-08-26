"""RootCause AI - Investigation Narrator Engine.

Converts verified numerical evidence from the deterministic investigation engine
into a clear, structured executive narrative using an LLM or a deterministic fallback.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Protocol

from apps.analytics.investigation.models import InvestigationResponse
from apps.analytics.narrator.models import InvestigationNarrative
from apps.analytics.narrator.prompt import build_narrator_prompt
from apps.api.config import get_settings
from scripts.eda_helpers import format_currency_brl

logger = logging.getLogger(__name__)

STANDARD_DISCLAIMER = (
    "This investigation report is synthesized from deterministic accounting "
    "marts and statistical contribution breakdowns. Observed dimensional "
    "contributions represent exact mathematical accounting associations and "
    "do not assert counterfactual causal identification."
)


class LLMProvider(Protocol):
    """Protocol for lightweight text generation providers."""

    def generate(self, prompt: str) -> str:
        """Generate raw text response from prompt."""
        ...


class OpenAICompatibleProvider:
    """Lightweight OpenAI REST client using standard library urllib."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 25.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Send chat completion request to OpenAI-compatible endpoint."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI Investigation Narrator. Return only a "
                        "valid JSON object matching the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return str(data["choices"][0]["message"]["content"])


class DeterministicFallbackNarrator:
    """Deterministic, rule-based narrator that formats verified evidence."""

    @classmethod
    def generate(cls, inv: InvestigationResponse) -> InvestigationNarrative:
        """Generate structured narrative directly from verified evidence."""
        metric_name = inv.request.metric.upper()
        cur_period = f"{inv.request.current_start} to {inv.request.current_end}"
        base_period = f"{inv.request.baseline_start} to {inv.request.baseline_end}"

        direction_word = inv.summary.direction.lower()
        tot_cur_str = (
            format_currency_brl(inv.summary.total_current)
            if "gmv" in inv.request.metric or "revenue" in inv.request.metric
            else f"{inv.summary.total_current:,.2f}"
        )
        tot_base_str = (
            format_currency_brl(inv.summary.total_baseline)
            if "gmv" in inv.request.metric or "revenue" in inv.request.metric
            else f"{inv.summary.total_baseline:,.2f}"
        )
        tot_chg_str = (
            format_currency_brl(abs(inv.summary.total_change))
            if "gmv" in inv.request.metric or "revenue" in inv.request.metric
            else f"{abs(inv.summary.total_change):,.2f}"
        )
        pct_str = (
            f"{inv.summary.total_change_pct:+.2f}%"
            if inv.summary.total_change_pct is not None
            else "N/A"
        )

        title = (
            f"Root-Cause Investigation: {metric_name} "
            f"{direction_word.capitalize()} ({pct_str})"
        )

        exec_summary = (
            f"{metric_name} shifted from {tot_base_str} in baseline ({base_period}) "
            f"to {tot_cur_str} in current period ({cur_period}), representing a "
            f"{direction_word} of {tot_chg_str} ({pct_str})."
        )

        num_dims = len(inv.analyses)
        anomaly_stmt = (
            f"The observed {direction_word} of {pct_str} was evaluated across "
            f"{num_dims} business dimensions to identify concentration drivers."
        )

        key_findings: list[str] = []
        root_causes: list[str] = []
        contributing_factors: list[str] = []
        evidence_refs: list[str] = [
            f"Current Period Total ({cur_period}): {tot_cur_str}",
            f"Baseline Period Total ({base_period}): {tot_base_str}",
            f"Absolute Metric Delta: {inv.summary.total_change:+,.2f} ({pct_str})",
        ]

        for analysis in inv.analyses:
            dim_label = analysis.dimension.replace("_", " ").title()

            # Positive drivers
            if analysis.top_positive_contributors:
                top_pos = analysis.top_positive_contributors[0]
                pos_chg = (
                    format_currency_brl(top_pos.absolute_change)
                    if "gmv" in inv.request.metric
                    else f"{top_pos.absolute_change:,.2f}"
                )
                contrib_p_str = (
                    f"{top_pos.contribution_pct:.2f}%"
                    if top_pos.contribution_pct is not None
                    else "N/A"
                )
                finding_pos = (
                    f"In {dim_label}, '{top_pos.value}' was the leading positive "
                    f"contributor with +{pos_chg} ({contrib_p_str} share)."
                )
                key_findings.append(finding_pos)
                if inv.summary.direction == "increase":
                    root_causes.append(
                        f"Growth in {dim_label} '{top_pos.value}' "
                        f"(+{pos_chg}, {contrib_p_str} share)."
                    )
                else:
                    contributing_factors.append(
                        f"Offsetting growth in {dim_label} '{top_pos.value}' "
                        f"(+{pos_chg})."
                    )
                evidence_refs.append(
                    f"Dimension [{analysis.dimension}] '{top_pos.value}': "
                    f"baseline={top_pos.baseline_value}, "
                    f"current={top_pos.current_value}, "
                    f"diff={top_pos.absolute_change}, contrib={contrib_p_str}"
                )

            # Negative drivers
            if analysis.top_negative_contributors:
                top_neg = analysis.top_negative_contributors[0]
                neg_chg = (
                    format_currency_brl(top_neg.absolute_change)
                    if "gmv" in inv.request.metric
                    else f"{top_neg.absolute_change:,.2f}"
                )
                contrib_n_str = (
                    f"{top_neg.contribution_pct:.2f}%"
                    if top_neg.contribution_pct is not None
                    else "N/A"
                )
                finding_neg = (
                    f"In {dim_label}, '{top_neg.value}' was the leading negative "
                    f"contributor with {neg_chg} ({contrib_n_str} share)."
                )
                key_findings.append(finding_neg)
                if inv.summary.direction == "decrease":
                    root_causes.append(
                        f"Decline in {dim_label} '{top_neg.value}' "
                        f"({neg_chg}, {contrib_n_str} share)."
                    )
                else:
                    contributing_factors.append(
                        f"Contraction in {dim_label} '{top_neg.value}' ({neg_chg})."
                    )
                evidence_refs.append(
                    f"Dimension [{analysis.dimension}] '{top_neg.value}': "
                    f"baseline={top_neg.baseline_value}, "
                    f"current={top_neg.current_value}, "
                    f"diff={top_neg.absolute_change}, contrib={contrib_n_str}"
                )

        if not key_findings:
            key_findings.append(
                "Metric remained stable with no dominant slice variance detected."
            )
        if not root_causes:
            root_causes.append(
                f"Overall {direction_word} was distributed evenly across slices."
            )

        recommendations = [
            "Conduct operational deep-dive on primary driver segments.",
            "Verify inventory availability and carrier SLA compliance.",
            "Monitor ongoing daily cohort trends to check persistence.",
        ]

        return InvestigationNarrative(
            title=title,
            executive_summary=exec_summary,
            anomaly_statement=anomaly_stmt,
            key_findings=key_findings,
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            recommended_next_steps=recommendations,
            evidence_references=evidence_refs,
            disclaimer=STANDARD_DISCLAIMER,
            narrator_type="deterministic_fallback",
        )


def generate_investigation_narrative(
    investigation: InvestigationResponse,
    provider: LLMProvider | None = None,
) -> InvestigationNarrative:
    """Generate structured narrative for investigation, with fallback."""
    settings = get_settings()

    active_provider = provider
    if active_provider is None and settings.llm_api_key:
        active_provider = OpenAICompatibleProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )

    if active_provider is not None:
        try:
            prompt = build_narrator_prompt(investigation)
            raw_response = active_provider.generate(prompt)
            data: dict[str, Any] = json.loads(raw_response)

            return InvestigationNarrative(
                title=str(data.get("title", "Investigation Report")),
                executive_summary=str(data.get("executive_summary", "")),
                anomaly_statement=str(data.get("anomaly_statement", "")),
                key_findings=list(data.get("key_findings", [])),
                root_causes=list(data.get("root_causes", [])),
                contributing_factors=list(data.get("contributing_factors", [])),
                recommended_next_steps=list(data.get("recommended_next_steps", [])),
                evidence_references=list(data.get("evidence_references", [])),
                disclaimer=str(data.get("disclaimer", STANDARD_DISCLAIMER)),
                narrator_type="llm",
            )
        except Exception as e:
            logger.warning(f"LLM narration failed ({e}). Using deterministic fallback.")

    return DeterministicFallbackNarrator.generate(investigation)
