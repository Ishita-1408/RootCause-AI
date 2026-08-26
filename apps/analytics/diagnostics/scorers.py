"""Scoring algorithms for Root-Cause Candidate Ranking.

Computes transparent, deterministic multi-factor root-cause scores based on
relative magnitude, contribution share, and signal consistency.
"""

from typing import Any

from apps.analytics.diagnostics.models import RootCauseFinding


def compute_root_cause_score(
    magnitude: float,
    contribution: float,
    consistency: float = 1.0,
    w_mag: float = 0.35,
    w_contrib: float = 0.45,
    w_consist: float = 0.20,
) -> float:
    """Calculate multi-factor deterministic score bounded in [0.0, 1.0].

    Args:
        magnitude: Relative percentage change normalized [0.0, 1.0].
        contribution: Share of total variance/change normalized [0.0, 1.0].
        consistency: Operational/data consistency confidence [0.0, 1.0].
        w_mag: Weight for relative magnitude.
        w_contrib: Weight for contribution share.
        w_consist: Weight for consistency.
    """
    clamped_mag = max(0.0, min(1.0, magnitude))
    clamped_contrib = max(0.0, min(1.0, contribution))
    clamped_consist = max(0.0, min(1.0, consistency))

    score = (
        (w_mag * clamped_mag)
        + (w_contrib * clamped_contrib)
        + (w_consist * clamped_consist)
    )
    return round(max(0.0, min(1.0, score)), 2)


def rank_candidate_root_causes(
    candidates: list[dict[str, Any]],
) -> list[RootCauseFinding]:
    """Rank candidates deterministically by multi-factor score descending."""
    candidates.sort(key=lambda x: float(x["score"]), reverse=True)

    findings: list[RootCauseFinding] = []
    for rank_idx, cand in enumerate(candidates, start=1):
        findings.append(
            RootCauseFinding(
                rank=rank_idx,
                cause=str(cand["cause"]),
                category=cand["category"],
                score=round(float(cand["score"]), 2),
                contribution=str(cand["contribution"]),
                evidence=str(cand["evidence"]),
            )
        )
    return findings
