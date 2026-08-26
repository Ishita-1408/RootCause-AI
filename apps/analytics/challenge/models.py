"""Pydantic data models for Forensic Challenge Mode (Phase M)."""

from typing import Any, Literal

from pydantic import BaseModel, Field

ChallengeType = Literal[
    "why_not_cause",
    "contradicting_evidence",
    "weakest_link",
    "what_would_change",
]


class ChallengeRequest(BaseModel):
    """User challenge query against a completed investigation conclusion."""

    session_id: str = Field(
        ..., description="Investigation session ID being challenged"
    )
    challenge_type: ChallengeType = Field(
        ...,
        description="Type of challenge to evaluate",
    )
    candidate_cause: str | None = Field(
        default=None,
        description="Alternative candidate cause (e.g. 'average_order_value')",
    )


class EvidenceEvaluation(BaseModel):
    """Specific evidence item evaluated under challenge scrutiny."""

    evidence_title: str
    observed_fact: str
    verdict: Literal[
        "supports_top_cause",
        "contradicts_candidate",
        "weak_link",
        "inconclusive",
    ]
    numerical_proof: str


class ChallengeResponse(BaseModel):
    """Structured, deterministic response to an executive challenge."""

    session_id: str
    challenge_type: ChallengeType
    challenge_question: str
    verdict_summary: str
    top_ranked_cause: str
    evaluations: list[EvidenceEvaluation] = Field(default_factory=list)
    confidence_impact: str = "Unchanged — evidence remains conclusive"
    recommended_action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
