"""Deterministic Claim-Level Verification Firewall for Investigation Agent."""

import logging
from datetime import date
from typing import Any

from apps.analytics.agent.models import EvidenceBackedClaim

logger = logging.getLogger(__name__)


def apply_claim_firewall(
    claims: list[EvidenceBackedClaim],
    evidence_pool: list[Any],
    scenario_date: date,
    allowed_tolerance: float = 0.05,
) -> tuple[list[EvidenceBackedClaim], list[str]]:
    """Filter claims through the deterministic verification firewall.

    Returns:
    (verified_claims, final_grounded_key_findings)
    """
    from evaluation.hallucination.models import StructuredClaim
    from evaluation.hallucination.verifier import verify_single_claim

    verified_claims: list[EvidenceBackedClaim] = []
    final_findings: list[str] = []

    for c in claims:
        # Convert EvidenceBackedClaim to StructuredClaim for verification
        s_claim = StructuredClaim(
            claim_id=f"firewall_chk_{c.evidence_id}",
            claim_type=c.claim_type,
            metric=c.metric,
            subject=c.subject,
            value=c.value,
            direction=c.direction,
            dimension=c.dimension,
            dimension_value=c.dimension_value,
            anomaly_date=scenario_date,
            comparison_window=7,
            evidence_ids=[c.evidence_id],
            causal_mechanism=c.causal_mechanism,
            derived_formula=c.derived_formula,
            causal_support_level=c.causal_support_level,
            statistical_test=c.statistical_test,
            p_value=c.p_value,
            confidence_interval=c.confidence_interval,
            effect_size=c.effect_size,
            sample_size=c.sample_size,
            evidence_strength=c.evidence_strength,
            causal_language_level=c.causal_language_level,
        )

        res = verify_single_claim(
            claim=s_claim,
            evidence_pool=evidence_pool,
            scenario_date=scenario_date,
            allowed_tolerance=allowed_tolerance,
        )

        if res.verification_status == "SUPPORTED":
            c.is_verified = True
            verified_claims.append(c)
            if c.subject not in final_findings:
                final_findings.append(c.subject)
        else:
            logger.warning(
                f"[CLAIM_FIREWALL_BLOCKED] {c.subject} -> "
                f"{res.verification_status}: {res.failure_reason}"
            )

    if not final_findings:
        final_findings.append("Insufficient evidence to support this conclusion.")

    return verified_claims, final_findings
