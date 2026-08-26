"""Causal Language Guardrails and Policy Enforcement for RootCause AI (Phase K).

Enforces strict semantic distinction between:
- Descriptive observation (what occurred)
- Statistical association (correlation / significant difference)
- Mechanistic decomposition (mathematical accounting identity)
- Causal identification (counterfactual / quasi-experimental proof)

Prohibits unsupported phrases like "X caused Y" unless causal support level is 'causal'.
"""

import re

from apps.analytics.statistics.models import CausalSupportLevel

# Regex patterns matching unsupported causal claims
FORBIDDEN_CAUSAL_PATTERNS = [
    (
        re.compile(r"\b(?:is|was)\s+the\s+direct\s+cause\s+of\b", re.IGNORECASE),
        "direct causal assertion",
    ),
    (re.compile(r"\bdirectly\s+caused\b", re.IGNORECASE), "direct causal assertion"),
    (
        re.compile(r"\b(?:has\s+)?caused\b", re.IGNORECASE),
        "unqualified causal assertion",
    ),
    (
        re.compile(
            r"\bis\s+responsible\s+for\s+(?:the\s+)?(?:drop|surge|increase|decrease|decline|loss|growth)\b",
            re.IGNORECASE,
        ),
        "unsupported responsibility claim",
    ),
    (re.compile(r"\bproves?\s+causality\b", re.IGNORECASE), "proof of causality claim"),
    (re.compile(r"\bcausal\s+proof\b", re.IGNORECASE), "proof of causality claim"),
    (re.compile(r"\bsolely\s+caused\b", re.IGNORECASE), "sole causation claim"),
]

# Replacements for automated sanitization into defensible terminology
CAUSAL_REPLACEMENTS = [
    (
        re.compile(r"\bdirectly\s+caused\b", re.IGNORECASE),
        "is the strongest supported driver of",
    ),
    (re.compile(r"\bcaused\b", re.IGNORECASE), "is associated with"),
    (
        re.compile(r"\bis\s+responsible\s+for\b", re.IGNORECASE),
        "explains the observed variance in",
    ),
    (
        re.compile(r"\bproves?\s+causality\b", re.IGNORECASE),
        "demonstrates statistically significant association",
    ),
]


def validate_causal_language(
    text: str,
    support_level: CausalSupportLevel = "associational",
) -> tuple[bool, str | None]:
    """Validate whether text complies with causal language guardrails.

    If support_level is 'causal', explicit causal assertions are allowed.
    If support_level is 'descriptive', 'associational', or 'mechanistic',
    unsupported causal verbs ('caused', 'responsible for') are strictly rejected.
    """
    if support_level == "causal":
        return True, None

    for pattern, description in FORBIDDEN_CAUSAL_PATTERNS:
        match = pattern.search(text)
        if match:
            forbidden_phrase = match.group(0)
            return False, (
                f"Unsupported causal language detected: '{forbidden_phrase}' "
                f"({description}). In an observational {support_level} analysis, use "
                f"controlled language ('associated with', 'concentrated in', "
                f"'is the strongest supported driver')."
            )

    return True, None


def sanitize_causal_language(text: str) -> str:
    """Deterministically rewrite unsupported causal verbs into compliant language."""
    sanitized = text
    for pattern, replacement in CAUSAL_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
