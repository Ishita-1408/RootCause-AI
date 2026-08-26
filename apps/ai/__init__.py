"""AI Investigation Package."""

from apps.ai.investigator import (
    extract_evidence_payload,
    investigate_with_ai,
)
from apps.ai.models import (
    AIInvestigationEvidence,
    AIInvestigationResponse,
)
from apps.ai.prompts import SYSTEM_PROMPT, build_investigation_prompt
from apps.ai.provider import (
    DeterministicFallbackProvider,
    LLMProvider,
    OpenAICompatibleProvider,
    get_default_provider,
)

__all__ = [
    "AIInvestigationEvidence",
    "AIInvestigationResponse",
    "DeterministicFallbackProvider",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "SYSTEM_PROMPT",
    "build_investigation_prompt",
    "extract_evidence_payload",
    "get_default_provider",
    "investigate_with_ai",
]
