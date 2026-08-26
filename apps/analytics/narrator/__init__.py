"""AI Investigation Narrator package."""

from apps.analytics.narrator.models import (
    InvestigationNarrative,
    NarrativeRequest,
)
from apps.analytics.narrator.narrator import (
    DeterministicFallbackNarrator,
    LLMProvider,
    OpenAICompatibleProvider,
    generate_investigation_narrative,
)
from apps.analytics.narrator.prompt import build_narrator_prompt

__all__ = [
    "DeterministicFallbackNarrator",
    "InvestigationNarrative",
    "LLMProvider",
    "NarrativeRequest",
    "OpenAICompatibleProvider",
    "build_narrator_prompt",
    "generate_investigation_narrative",
]
