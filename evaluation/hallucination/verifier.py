"""Deterministic Claim-Level Hallucination Verifier Engine for Phase G."""

from datetime import date

from evaluation.hallucination.models import (
    ClaimBenchmarkSummary,
    ClaimVerificationResult,
    EvidenceRecord,
    StructuredClaim,
)


def verify_single_claim(
    claim: StructuredClaim,
    evidence_pool: list[EvidenceRecord],
    scenario_date: date | None = None,
    allowed_tolerance: float = 0.05,
) -> ClaimVerificationResult:
    """Deterministically verify a structured claim against an evidence pool.

    Evaluates:
    1. Evidence attribution validity (evidence_id existence & domain match)
    2. Date & comparison window alignment (detects temporal leaks)
    3. Metric & dimension / dimension_value alignment
    4. Directional consistency (detects explicit contradictions)
    5. Exact numerical accuracy & derived formula recalculation
    6. Causal mechanism validity
    """
    # 1. Evidence Matching
    matched_evidence: EvidenceRecord | None = None

    # Try explicit evidence_id lookup first
    if claim.evidence_ids:
        for eid in claim.evidence_ids:
            found = next((e for e in evidence_pool if e.evidence_id == eid), None)
            if found:
                matched_evidence = found
                break

    # If no ID or ID not found, match by semantic attributes
    if not matched_evidence:
        candidates = [
            e for e in evidence_pool if e.metric.lower() == claim.metric.lower()
        ]
        if claim.dimension:
            candidates = [
                e
                for e in candidates
                if (e.dimension or "").lower() == (claim.dimension or "").lower()
            ]
        if claim.dimension_value:
            candidates = [
                e
                for e in candidates
                if (e.dimension_value or "").lower()
                == (claim.dimension_value or "").lower()
            ]
        if claim.anomaly_date:
            candidates = [e for e in candidates if e.anomaly_date == claim.anomaly_date]

        if candidates:
            matched_evidence = candidates[0]

    # If still no evidence found, mark UNSUPPORTED
    if not matched_evidence:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="UNSUPPORTED",
            claimed_value=claim.value,
            evidence_value=None,
            absolute_error=None,
            relative_error_pct=None,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                f"No supporting evidence found for metric '{claim.metric}' "
                f"(dim={claim.dimension}, val={claim.dimension_value}, "
                f"date={claim.anomaly_date})."
            ),
            evidence_matched_id=None,
        )

    # 1.5 Causal Language Guardrail Check (Phase K)
    from apps.analytics.statistics.causal_guardrails import validate_causal_language

    is_valid_causal, causal_err = validate_causal_language(
        text=claim.subject,
        support_level=claim.causal_support_level,
    )
    if not is_valid_causal:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="UNSUPPORTED",
            claimed_value=claim.value,
            evidence_value=matched_evidence.observed_value,
            allowed_tolerance=allowed_tolerance,
            failure_reason=causal_err,
            evidence_matched_id=matched_evidence.evidence_id,
        )

    # 1.6 Statistical Significance & Confidence Interval Integrity (Phase K)
    subj_lower = claim.subject.lower()
    is_sig_claimed = any(
        w in subj_lower
        for w in [
            "statistically significant",
            "statistically substantial",
            "significant shift",
            "significant difference",
        ]
    )

    p_val = claim.p_value if claim.p_value is not None else matched_evidence.p_value
    if is_sig_claimed and p_val is not None and p_val > 0.05:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="UNSUPPORTED",
            claimed_value=claim.value,
            evidence_value=matched_evidence.observed_value,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                f"Statistical contradiction: Claim asserts statistical significance, "
                f"but p-value ({p_val:.4f}) exceeds the alpha threshold (0.05)."
            ),
            evidence_matched_id=matched_evidence.evidence_id,
        )

    ci = claim.confidence_interval or matched_evidence.confidence_interval
    if is_sig_claimed and ci and len(ci) >= 2:
        if ci[0] < 0.0 < ci[1]:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="UNSUPPORTED",
                claimed_value=claim.value,
                evidence_value=matched_evidence.observed_value,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    f"Statistical contradiction: Claim asserts significance, but the "
                    f"confidence interval [{ci[0]:.2f}, {ci[1]:.2f}] crosses zero."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

    n_samp = (
        claim.sample_size
        if claim.sample_size is not None
        else matched_evidence.sample_size
    )
    if is_sig_claimed and n_samp is not None and n_samp < 2:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="UNSUPPORTED",
            claimed_value=claim.value,
            evidence_value=matched_evidence.observed_value,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                f"Statistical contradiction: Claim asserts significance, but "
                f"sample size (n={n_samp}) is insufficient for inference."
            ),
            evidence_matched_id=matched_evidence.evidence_id,
        )

    # 1.7 Practical Significance Check (Phase K)
    eff_size = (
        claim.effect_size
        if claim.effect_size is not None
        else matched_evidence.effect_size
    )
    if (
        any(
            w in subj_lower
            for w in ["primary driver", "major impact", "dominant shift"]
        )
        and eff_size is not None
        and abs(eff_size) < 0.01
    ):
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="UNSUPPORTED",
            claimed_value=claim.value,
            evidence_value=matched_evidence.observed_value,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                "Practical significance failure: Claim asserts primary driver, "
                f"but observed effect size ({eff_size}) is practically negligible."
            ),
            evidence_matched_id=matched_evidence.evidence_id,
        )

    # 1.8 Change-Point & Persistence Integrity Check (Phase L)
    is_cp_claimed = any(
        w in subj_lower
        for w in [
            "change point detected on",
            "regime shift on",
            "structural change on",
            "persistent regime shift",
        ]
    )
    if is_cp_claimed:
        raw_det = matched_evidence.raw_details.get("change_point_detected", False)
        raw_regime = matched_evidence.raw_details.get("regime_type", "normal")
        raw_persist = matched_evidence.raw_details.get(
            "persistence", "INSUFFICIENT_EVIDENCE"
        )

        if not raw_det and any(
            w in subj_lower for w in ["change point detected", "regime shift on"]
        ):
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="UNSUPPORTED",
                claimed_value=claim.value,
                evidence_value=matched_evidence.observed_value,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    "Change-point contradiction: Claim asserts structural break, "
                    "but analytical evidence confirms no change point occurred."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

        if "persistent regime shift" in subj_lower and (
            raw_persist == "SPIKE" or raw_regime == "isolated_anomaly"
        ):
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="UNSUPPORTED",
                claimed_value=claim.value,
                evidence_value=matched_evidence.observed_value,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    "Persistence contradiction: Claim asserts persistent regime shift, "
                    "but analytical evidence confirms an isolated spike."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

    # 2. Date & Temporal Window Integrity Check
    target_date = claim.anomaly_date or scenario_date
    if target_date and matched_evidence.anomaly_date != target_date:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="CONTRADICTED",
            claimed_value=claim.value,
            evidence_value=matched_evidence.observed_value,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                f"Evidence date mismatch (Scenario: {target_date}, "
                f"Evidence: {matched_evidence.anomaly_date}). Temporal leak."
            ),
            evidence_matched_id=matched_evidence.evidence_id,
        )

    # 3. Directional Contradiction Check
    if claim.direction and matched_evidence.direction:
        c_dir = claim.direction.lower()
        e_dir = matched_evidence.direction.lower()
        if (c_dir == "increase" and e_dir == "decrease") or (
            c_dir == "decrease" and e_dir == "increase"
        ):
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="CONTRADICTED",
                claimed_value=claim.value,
                evidence_value=matched_evidence.observed_value,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    f"Directional contradiction: Claim asserts '{claim.direction}' "
                    f"while evidence proves '{matched_evidence.direction}'."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

    # 4. Dimension Slice Contradiction Check
    if claim.dimension and matched_evidence.dimension:
        if claim.dimension.lower() != matched_evidence.dimension.lower():
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="CONTRADICTED",
                claimed_value=claim.value,
                evidence_value=None,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    f"Dimension mismatch: Claim specifies '{claim.dimension}' "
                    f"but evidence belongs to '{matched_evidence.dimension}'."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

    # Macro causal mechanisms contain display text rather than raw identifiers
    is_macro_mechanism = (claim.dimension or "").lower() in (
        "order_volume",
        "average_order_value",
        "delivery",
        "pricing",
    )
    has_diff_dim_val = (
        not is_macro_mechanism
        and claim.dimension_value
        and matched_evidence.dimension_value
        and (claim.dimension_value.lower() != matched_evidence.dimension_value.lower())
    )
    if has_diff_dim_val:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            verification_status="CONTRADICTED",
            claimed_value=claim.value,
            evidence_value=None,
            allowed_tolerance=allowed_tolerance,
            failure_reason=(
                f"Dimension value mismatch: Claim specifies '{claim.dimension_value}' "
                f"but evidence is for '{matched_evidence.dimension_value}'."
            ),
            evidence_matched_id=matched_evidence.evidence_id,
        )

    # 5. Numerical Value & Derived Formula Verification
    if claim.value is not None:
        expected_val: float | None = None

        if claim.derived_formula == "percentage_change":
            if (
                matched_evidence.baseline_value is not None
                and abs(matched_evidence.baseline_value) > 1e-9
            ):
                expected_val = (
                    (matched_evidence.observed_value - matched_evidence.baseline_value)
                    / matched_evidence.baseline_value
                ) * 100.0
            elif matched_evidence.delta_pct is not None:
                expected_val = matched_evidence.delta_pct
        elif claim.derived_formula == "absolute_change":
            if matched_evidence.baseline_value is not None:
                expected_val = (
                    matched_evidence.observed_value - matched_evidence.baseline_value
                )
            elif matched_evidence.delta is not None:
                expected_val = matched_evidence.delta
        elif claim.derived_formula == "contribution_percentage":
            if matched_evidence.raw_details.get("contribution_pct") is not None:
                expected_val = float(matched_evidence.raw_details["contribution_pct"])
            elif matched_evidence.delta_pct is not None:
                expected_val = matched_evidence.delta_pct
        elif claim.derived_formula in ("volume_effect", "aov_effect"):
            key = (
                "volume_effect"
                if claim.derived_formula == "volume_effect"
                else "aov_effect"
            )
            if matched_evidence.raw_details.get(key) is not None:
                expected_val = float(matched_evidence.raw_details[key])
        else:
            expected_val = matched_evidence.observed_value

        if expected_val is not None:
            claimed_val = claim.value
            abs_err = abs(claimed_val - expected_val)
            denom = abs(expected_val) if abs(expected_val) > 1e-6 else 1.0
            rel_err_pct = (abs_err / denom) * 100.0

            # Sign mismatch check
            if (
                (claimed_val > 0 and expected_val < 0)
                or (claimed_val < 0 and expected_val > 0)
            ) and abs_err > 1.0:
                return ClaimVerificationResult(
                    claim_id=claim.claim_id,
                    verification_status="CONTRADICTED",
                    claimed_value=claimed_val,
                    evidence_value=expected_val,
                    absolute_error=round(abs_err, 4),
                    relative_error_pct=round(rel_err_pct, 2),
                    allowed_tolerance=allowed_tolerance,
                    failure_reason=(
                        f"Sign contradiction: Claimed {claimed_val:+.2f} contradicts "
                        f"empirical truth {expected_val:+.2f}."
                    ),
                    evidence_matched_id=matched_evidence.evidence_id,
                )

            # Numerical tolerance check (relative tolerance or small absolute tolerance)
            is_accurate = (rel_err_pct <= (allowed_tolerance * 100.0)) or (
                abs_err <= 1.0 and abs(expected_val) <= 100.0
            )

            if is_accurate:
                return ClaimVerificationResult(
                    claim_id=claim.claim_id,
                    verification_status="SUPPORTED",
                    claimed_value=claimed_val,
                    evidence_value=round(expected_val, 4),
                    absolute_error=round(abs_err, 4),
                    relative_error_pct=round(rel_err_pct, 2),
                    allowed_tolerance=allowed_tolerance,
                    failure_reason=None,
                    evidence_matched_id=matched_evidence.evidence_id,
                )
            elif rel_err_pct <= 25.0:
                return ClaimVerificationResult(
                    claim_id=claim.claim_id,
                    verification_status="PARTIALLY_SUPPORTED",
                    claimed_value=claimed_val,
                    evidence_value=round(expected_val, 4),
                    absolute_error=round(abs_err, 4),
                    relative_error_pct=round(rel_err_pct, 2),
                    allowed_tolerance=allowed_tolerance,
                    failure_reason=(
                        f"Numerical imprecision: Claimed {claimed_val} differs from "
                        f"evidence value {expected_val:.2f} by {rel_err_pct:.1f}%."
                    ),
                    evidence_matched_id=matched_evidence.evidence_id,
                )
            else:
                return ClaimVerificationResult(
                    claim_id=claim.claim_id,
                    verification_status="CONTRADICTED"
                    if rel_err_pct >= 50.0
                    else "UNSUPPORTED",
                    claimed_value=claimed_val,
                    evidence_value=round(expected_val, 4),
                    absolute_error=round(abs_err, 4),
                    relative_error_pct=round(rel_err_pct, 2),
                    allowed_tolerance=allowed_tolerance,
                    failure_reason=(
                        f"Fabricated / Incorrect number: Claimed {claimed_val} vs "
                        f"ground truth {expected_val:.2f} (Error: {rel_err_pct:.1f}%)."
                    ),
                    evidence_matched_id=matched_evidence.evidence_id,
                )

    # 6. Qualitative / Causal Claim Validation
    if claim.claim_type == "causal" and claim.causal_mechanism:
        mech = claim.causal_mechanism.lower()
        if (
            "dominant_mechanism" in matched_evidence.raw_details
            and matched_evidence.raw_details["dominant_mechanism"] != mech
        ):
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                verification_status="CONTRADICTED",
                claimed_value=None,
                evidence_value=None,
                allowed_tolerance=allowed_tolerance,
                failure_reason=(
                    f"Causal contradiction: Claim asserts '{claim.causal_mechanism}' "
                    f"while analytical decomposition proves "
                    f"'{matched_evidence.raw_details['dominant_mechanism']}'."
                ),
                evidence_matched_id=matched_evidence.evidence_id,
            )

    return ClaimVerificationResult(
        claim_id=claim.claim_id,
        verification_status="SUPPORTED",
        claimed_value=claim.value,
        evidence_value=matched_evidence.observed_value,
        absolute_error=0.0,
        relative_error_pct=0.0,
        allowed_tolerance=allowed_tolerance,
        failure_reason=None,
        evidence_matched_id=matched_evidence.evidence_id,
    )


def evaluate_claims_against_evidence(
    claims: list[StructuredClaim],
    evidence_pool: list[EvidenceRecord],
    scenario_date: date | None = None,
    allowed_tolerance: float = 0.05,
) -> ClaimBenchmarkSummary:
    """Evaluate a batch of structured claims and compile aggregate forensic metrics."""
    if not claims:
        return ClaimBenchmarkSummary(
            total_claims=0,
            supported_count=0,
            partially_supported_count=0,
            unsupported_count=0,
            contradicted_count=0,
            claim_grounding_rate=100.0,
            unsupported_claim_rate=0.0,
            contradiction_rate=0.0,
            hallucination_rate=0.0,
            numerical_accuracy=100.0,
            evidence_attribution_accuracy=100.0,
            claim_precision=100.0,
            claim_recall=100.0,
            results=[],
        )

    results: list[ClaimVerificationResult] = []
    num_checked = 0
    num_accurate = 0
    valid_attributions = 0
    total_attributions = 0

    for claim in claims:
        res = verify_single_claim(
            claim=claim,
            evidence_pool=evidence_pool,
            scenario_date=scenario_date,
            allowed_tolerance=allowed_tolerance,
        )
        results.append(res)

        if claim.value is not None:
            num_checked += 1
            if res.verification_status in ("SUPPORTED", "PARTIALLY_SUPPORTED"):
                num_accurate += 1

        if claim.evidence_ids:
            total_attributions += len(claim.evidence_ids)
            if res.evidence_matched_id in claim.evidence_ids:
                valid_attributions += 1

    n = len(claims)
    supp = sum(1 for r in results if r.verification_status == "SUPPORTED")
    part = sum(1 for r in results if r.verification_status == "PARTIALLY_SUPPORTED")
    unsupp = sum(1 for r in results if r.verification_status == "UNSUPPORTED")
    contra = sum(1 for r in results if r.verification_status == "CONTRADICTED")

    grounding_rate = ((supp + part) / n) * 100.0
    unsupp_rate = (unsupp / n) * 100.0
    contra_rate = (contra / n) * 100.0
    hallucination_rate = ((unsupp + contra) / n) * 100.0

    num_acc = (num_accurate / num_checked * 100.0) if num_checked > 0 else 100.0
    attr_acc = (
        (valid_attributions / total_attributions * 100.0)
        if total_attributions > 0
        else 100.0
    )
    precision = (supp / max(supp + unsupp + contra, 1)) * 100.0
    recall = (supp / n) * 100.0

    return ClaimBenchmarkSummary(
        total_claims=n,
        supported_count=supp,
        partially_supported_count=part,
        unsupported_count=unsupp,
        contradicted_count=contra,
        claim_grounding_rate=round(grounding_rate, 2),
        unsupported_claim_rate=round(unsupp_rate, 2),
        contradiction_rate=round(contra_rate, 2),
        hallucination_rate=round(hallucination_rate, 2),
        numerical_accuracy=round(num_acc, 2),
        evidence_attribution_accuracy=round(attr_acc, 2),
        claim_precision=round(precision, 2),
        claim_recall=round(recall, 2),
        results=results,
    )
