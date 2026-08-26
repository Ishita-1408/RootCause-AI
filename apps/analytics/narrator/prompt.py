"""Prompt templates for RootCause AI Investigation Narrator."""

import json

from apps.analytics.investigation.models import InvestigationResponse

SYSTEM_INSTRUCTION = """\
You are the AI Investigation Narrator for RootCause AI, an autonomous business \
investigation platform.
Your sole mission is to explain verified numerical evidence in clear, professional \
executive business language.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. STRICT EVIDENCE CONTRACT: You are strictly an explanation layer. Use ONLY \
the supplied evidence in the prompt. Do NOT invent, hallucinate, extrapolate, \
or estimate metrics, causes, dates, percentages, customer names, or business facts.
2. NO CAUSALITY FROM ASSOCIATION: Clearly distinguish correlation and dimensional \
contribution from causation. Do NOT claim causality unless explicitly proven \
(e.g., write "Credit-card transactions were the largest observed contributor", \
NEVER "Credit cards caused the increase").
3. ACCURACY: Every figure and percentage cited in your narrative must match \
the evidence JSON with 100% fidelity.
4. FORMAT: Return ONLY a valid JSON object conforming to the schema below.
"""

NARRATIVE_SCHEMA_DOC = """\
Expected JSON Output Schema:
{
  "title": "<Concise descriptive title>",
  "executive_summary": "<2-3 sentence executive briefing>",
  "anomaly_statement": "<1-2 sentences on observed delta and change percentage>",
  "key_findings": ["<Key bullet 1>", "<Key bullet 2>", ...],
  "root_causes": ["<Primary observed driver 1>", "<Primary observed driver 2>", ...],
  "contributing_factors": ["<Secondary/offsetting driver 1>", ...],
  "recommended_next_steps": ["<Actionable recommendation 1>", ...],
  "evidence_references": ["<Exact verified metric citations>", ...],
  "disclaimer": "This analysis reflects observed statistical contributions and descriptive decompositions from verified platform transactional data. Observed dimensional contributions represent mathematical accounting associations and do not assert counterfactual causal identification."
}
"""  # noqa: E501


def build_narrator_prompt(investigation: InvestigationResponse) -> str:
    """Construct structured explanation prompt containing only verified evidence."""
    evidence_json = json.dumps(investigation.model_dump(mode="json"), indent=2)

    return f"""{SYSTEM_INSTRUCTION}

{NARRATIVE_SCHEMA_DOC}

============================================================
VERIFIED NUMERICAL EVIDENCE (IMMUTABLE SOURCE OF TRUTH):
============================================================
{evidence_json}
============================================================

Generate the structured JSON InvestigationNarrative strictly from evidence above:
"""
