"""LLM Provider abstraction and implementations for RootCause AI."""

import json
import logging
import os
from typing import Protocol

import httpx

from apps.ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol defining the LLM provider interface."""

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Generate a response text from prompt and system prompt."""
        ...


class OpenAICompatibleProvider:
    """HTTP client for OpenAI-compatible LLM endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "LLM_API_KEY is not configured. Please set the "
                "LLM_API_KEY environment variable."
            )

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Call the LLM chat completions API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return str(content)
        except Exception as e:
            # Mask API key from logs
            logger.error(f"Error in LLM call (model={self.model}): {type(e).__name__}")
            raise


class DeterministicFallbackProvider:
    """Offline deterministic fallback provider for zero-API-key execution."""

    def __init__(self, model_name: str = "deterministic-rule-synthesizer") -> None:
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Synthesize structured JSON report directly from evidence in prompt."""
        payload_data: dict[str, object] = {}
        try:
            if "VERIFIED EVIDENCE PAYLOAD:" in prompt:
                evidence_text = prompt.split("VERIFIED EVIDENCE PAYLOAD:")[1]
                if "INSTRUCTIONS:" in evidence_text:
                    evidence_text = evidence_text.split("INSTRUCTIONS:")[0]
                payload_data = json.loads(evidence_text.strip())
        except Exception:
            payload_data = {}

        metric_name = str(payload_data.get("metric", "metric")).upper()
        anomaly_date = str(payload_data.get("anomaly_date", "target date"))
        chg_pct = payload_data.get("percentage_change")
        direction = str(payload_data.get("direction", "movement"))
        pct_str = f"{chg_pct:+.1f}%" if chg_pct is not None else "N/A"

        orders_pct_raw = payload_data.get("orders_change_pct")
        aov_pct_raw = payload_data.get("aov_change_pct")
        orders_pct = (
            float(orders_pct_raw) if isinstance(orders_pct_raw, (int, float)) else None
        )
        aov_pct = float(aov_pct_raw) if isinstance(aov_pct_raw, (int, float)) else None

        orders_pct_str = f"{orders_pct:+.1f}%" if orders_pct is not None else "N/A"
        aov_pct_str = f"{aov_pct:+.1f}%" if aov_pct is not None else "N/A"

        top_contribs = payload_data.get("top_contributors", [])
        if isinstance(top_contribs, list) and top_contribs:
            first = top_contribs[0]
            if isinstance(first, dict):
                dim_k = first.get("dimension")
                dim_v = first.get("dimension_value")
                top_dim_str = f"{dim_k}: {dim_v}"
            else:
                top_dim_str = "commercial categories and regional cohorts"
        else:
            top_dim_str = "commercial categories and regional cohorts"

        op_data = payload_data.get("operational_indicators", {})
        late_obs = (
            float(op_data.get("observed_late_delivery_rate", 0.0))
            if isinstance(op_data, dict)
            else 0.0
        )
        late_base = (
            float(op_data.get("baseline_late_delivery_rate", 0.0))
            if isinstance(op_data, dict)
            else 0.0
        )

        vol_eff_raw = payload_data.get("volume_effect")
        aov_eff_raw = payload_data.get("aov_effect")
        vol_eff = float(vol_eff_raw) if isinstance(vol_eff_raw, (int, float)) else None
        aov_eff = float(aov_eff_raw) if isinstance(aov_eff_raw, (int, float)) else None

        vol_mag = (
            abs(vol_eff)
            if vol_eff is not None
            else (abs(orders_pct) if orders_pct is not None else 0.0)
        )
        aov_mag = (
            abs(aov_eff)
            if aov_eff is not None
            else (abs(aov_pct) if aov_pct is not None else 0.0)
        )
        is_vol_dominant = vol_mag >= aov_mag

        # Determine driver descriptions
        if is_vol_dominant:
            primary_finding = f"Order volume shifted {orders_pct_str} (primary driver)."
            secondary_finding = (
                f"Average Order Value (AOV) shifted {aov_pct_str} (secondary factor)."
            )
            if orders_pct is not None and orders_pct >= 0:
                interpretations = [
                    "Observed movement is driven by order volume expansion.",
                    f"Basket sizes shifted {aov_pct_str} across product categories.",
                    "Logistics throughput was tested by increased demand.",
                ]
                actions = [
                    "Align fulfillment capacity buffers for forecasted volume surges.",
                    "Audit marketing acquisition channels driving the order increase.",
                    "Monitor post-event delivery lead times to protect CX.",
                ]
            else:
                interpretations = [
                    "Observed movement is driven by order volume contraction.",
                    f"Basket sizes shifted {aov_pct_str} across product categories.",
                    "Demand drop may indicate channel outages or fatigue.",
                ]
                actions = [
                    "Audit marketing acquisition funnel and conversion drop-offs.",
                    "Investigate payment gateway authorization rates.",
                    "Review competitor promotions and seasonal category trends.",
                ]
        else:
            primary_finding = (
                f"Average Order Value (AOV) shifted {aov_pct_str} (primary driver)."
            )
            secondary_finding = (
                f"Order volume shifted {orders_pct_str} (secondary factor)."
            )
            if aov_pct is not None and aov_pct >= 0:
                interpretations = [
                    "Observed movement is driven by basket value expansion.",
                    f"Order volume shifted {orders_pct_str} during the period.",
                    "Higher-ticket item adoption lifted average basket size.",
                ]
                actions = [
                    "Analyze product category mix driving basket expansion.",
                    "Review pricing strategy and bundle cross-sell attach rates.",
                    "Maintain healthy inventory levels for high-ticket items.",
                ]
            else:
                interpretations = [
                    "Observed movement is driven by average basket size contraction.",
                    f"Order volume shifted {orders_pct_str} during the period.",
                    "Heavy discounting or lower-priced item shifts reduced baskets.",
                ]
                actions = [
                    "Audit promotional discount depth and margin degradation.",
                    "Review product pricing tiers and basket attach rates.",
                    "Assess whether promotional mix is cannibalizing full-price items.",
                ]

        title = f"Root-Cause Investigation: {metric_name} Anomaly ({anomaly_date})"
        summary = (
            f"{metric_name} experienced a substantial {direction} of {pct_str} on "
            f"{anomaly_date}. Decomposition indicates order volume shifted "
            f"{orders_pct_str} while AOV moved {aov_pct_str}. "
            f"The movement was primarily concentrated in {top_dim_str}."
        )

        synth = {
            "investigation_title": title,
            "executive_summary": summary,
            "key_findings": [
                f"Headline {metric_name} shifted {pct_str} on {anomaly_date} vs base.",
                primary_finding,
                secondary_finding,
                f"Late delivery rate stood at {late_obs:.1f}% vs {late_base:.1f}%.",
            ],
            "business_interpretation": interpretations,
            "recommended_actions": actions,
            "limitations": [
                "Findings identify mathematical contributions, not causality.",
                "Single-day observed aggregates are sensitive to seasonality.",
            ],
        }
        return json.dumps(synth)


def get_default_provider() -> LLMProvider:
    """Return OpenAI provider if key is set, else deterministic fallback."""
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if api_key:
        return OpenAICompatibleProvider(api_key=api_key)
    return DeterministicFallbackProvider()
