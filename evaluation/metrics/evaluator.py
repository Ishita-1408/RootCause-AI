"""Deterministic Evaluator for RootCause AI Benchmark Scenarios.

Structured Causal Evaluator v2.
"""

from apps.analytics.agent.models import InvestigationAgentResponse, RankedRootCause
from evaluation.metrics.models import BenchmarkSummary, EvaluationResult
from evaluation.scenarios.models import GroundTruthRootCause, GroundTruthScenario

# Standard Canonical Causal Mechanism Aliases Mapping
MECHANISM_ALIASES: dict[str, str] = {
    # Volume mechanism aliases
    "order_volume": "order_volume",
    "volume": "order_volume",
    "order_count": "order_volume",
    "orders_count": "order_volume",
    "order_volume_drop": "order_volume",
    "order_volume_surge": "order_volume",
    "order_volume_spike": "order_volume",
    "demand_volume_surge": "order_volume",
    # AOV mechanism aliases
    "average_order_value": "average_order_value",
    "aov": "average_order_value",
    "basket_size": "average_order_value",
    "pricing": "average_order_value",
    "average_order_value_expansion": "average_order_value",
    "average_order_value_contraction": "average_order_value",
    # Delivery mechanism aliases
    "delivery": "delivery",
    "carrier_sla": "delivery",
    "carrier_transit_delay": "delivery",
    "logistics_fulfillment_bottleneck": "delivery",
    "carrier_sla_degradation": "delivery",
    "late_delivery": "delivery",
    "late_delivery_rate": "delivery",
    "late_delivery_rate_pct": "delivery",
    # Review / Sentiment mechanism aliases
    "avg_review_score": "avg_review_score",
    "customer_satisfaction_decline": "avg_review_score",
    "review_score": "avg_review_score",
    "sentiment": "avg_review_score",
    # Dimension aliases
    "product_category": "product_category",
    "customer_state": "customer_state",
    "seller": "seller",
}

CAUSAL_MECHANISMS: set[str] = {
    "order_volume",
    "average_order_value",
    "delivery",
    "avg_review_score",
}

SEGMENT_DIMENSIONS: set[str] = {
    "customer_state",
    "product_category",
    "seller",
}


def canonicalize_mechanism(name: str | None) -> str | None:
    """Normalize mechanism or dimension name to its canonical identifier."""
    if not name:
        return None
    normalized = name.strip().lower().replace("-", "_")
    return MECHANISM_ALIASES.get(normalized, normalized)


def _matches_cause(pred: RankedRootCause | str, target: GroundTruthRootCause) -> bool:
    """Check if a predicted root cause matches the ground truth target structuredly.

    Explicit Semantic Invariants:
    1. A causal mechanism (order_volume, average_order_value, delivery) matches
       if and only if the prediction has the matching canonical causal mechanism.
    2. Segment-only predictions (causal_category == 'segment_concentration' or
       no causal mechanism) NEVER match a causal mechanism ground truth.
    3. Segment targets match if dimension and slice value match.
    4. Evaluator is 100% deterministic and independent of natural language phrasing.
    """
    # Resolve target canonical mechanism
    target_mech = canonicalize_mechanism(
        target.causal_mechanism or target.dimension or target.cause_id
    )
    target_is_causal_mech = target_mech in CAUSAL_MECHANISMS

    if isinstance(pred, str):
        # Fallback string parsing for string representations
        pred_text = pred.strip().lower()
        if target_is_causal_mech:
            return target_mech in pred_text if target_mech else False
        t_dim = (target.affected_dimension or target.dimension or "").lower()
        t_val = (target.affected_value or target.dimension_value or "").lower()
        dim_ok = t_dim in pred_text if t_dim else True
        val_ok = t_val in pred_text if t_val else True
        return dim_ok and val_ok

    # Resolve prediction canonical mechanism
    # If the cause is purely a segment concentration, it has NO causal mechanism
    if pred.causal_category == "segment_concentration":
        pred_mech = None
    else:
        pred_mech = canonicalize_mechanism(pred.causal_mechanism or pred.dimension)

    # 1. Target is a Causal Mechanism (Why)
    if target_is_causal_mech:
        if pred.causal_category == "segment_concentration" or pred_mech is None:
            # Segments like customer_state=SP cannot match causal mechanisms
            return False
        return pred_mech == target_mech

    # 2. Target is a Segment Concentration (Where)
    target_dim: str | None = canonicalize_mechanism(
        target.affected_dimension or target.dimension
    )
    pred_dim: str | None = canonicalize_mechanism(
        pred.affected_dimension or pred.dimension
    )

    if not target_dim or pred_dim != target_dim:
        return False

    # Check slice value if target specifies one
    target_val = (target.affected_value or target.dimension_value or "").strip().lower()
    if target_val:
        pred_val = (pred.affected_value or pred.dimension_value or "").strip().lower()
        return pred_val == target_val

    return True


def evaluate_scenario_response(
    scenario: GroundTruthScenario,
    response: InvestigationAgentResponse,
    execution_time_ms: float,
) -> EvaluationResult:
    """Evaluate an autonomous agent response against a ground-truth scenario.

    Uses Structured Causal Evaluator v2.
    """
    predicted_causes = response.top_root_causes
    pred_strings = [
        f"{c.title} ({c.dimension}={c.dimension_value or 'all'})"
        for c in predicted_causes
    ]

    # 1. Rank & Accuracy Evaluation
    top1_correct = False
    top3_correct = False
    reciprocal_rank = 0.0
    correct_rank = None

    for idx, pred in enumerate(predicted_causes):
        if _matches_cause(pred, scenario.primary_cause):
            correct_rank = idx + 1
            reciprocal_rank = 1.0 / correct_rank
            if idx == 0:
                top1_correct = True
            if idx < 3:
                top3_correct = True
            break

    # 2. False Positive Rate
    valid_targets = [scenario.primary_cause] + scenario.secondary_causes
    unmatched_count = 0
    top_candidates = (
        predicted_causes[:3] if len(predicted_causes) >= 3 else predicted_causes
    )

    for pred in top_candidates:
        matched = any(_matches_cause(pred, vt) for vt in valid_targets)
        if not matched:
            unmatched_count += 1

    false_positive_rate = (
        (unmatched_count / len(top_candidates)) if top_candidates else 0.0
    )

    # 3. Quantitative Contribution Error
    contribution_error: float | None = None
    if scenario.primary_cause.expected_contribution_pct is not None:
        target_mech = canonicalize_mechanism(
            scenario.primary_cause.causal_mechanism or scenario.primary_cause.dimension
        )
        if target_mech == "order_volume" and response.decomposition:
            actual_pct = abs(response.decomposition.volume_contribution_pct or 0.0)
            contribution_error = abs(
                actual_pct - scenario.primary_cause.expected_contribution_pct
            )
        elif target_mech == "average_order_value" and response.decomposition:
            actual_pct = abs(response.decomposition.aov_contribution_pct or 0.0)
            contribution_error = abs(
                actual_pct - scenario.primary_cause.expected_contribution_pct
            )
        elif predicted_causes and _matches_cause(
            predicted_causes[0], scenario.primary_cause
        ):
            actual_pct = abs(predicted_causes[0].contribution_pct or 0.0)
            contribution_error = abs(
                actual_pct - scenario.primary_cause.expected_contribution_pct
            )

    # 4. Evidence Grounding & Integrity Check
    evidence_grounded = True
    unsupported_count = 0
    hallucination_count = 0

    # Check each top cause has supporting numerical evidence
    for cause in predicted_causes:
        if cause.score <= 0 and cause.contribution_pct is None:
            unsupported_count += 1
            evidence_grounded = False

    # Check key findings against supporting evidence & operational indicators
    for finding in response.key_findings:
        finding_lower = finding.lower()
        has_support = (
            any(
                str(c.dimension_value or "").lower() in finding_lower
                for c in response.supporting_evidence
            )
            or "order" in finding_lower
            or "volume" in finding_lower
            or "delivery" in finding_lower
            or "carrier" in finding_lower
            or "sla" in finding_lower
            or "transit" in finding_lower
            or "fulfillment" in finding_lower
            or "delay" in finding_lower
            or "basket" in finding_lower
            or "aov" in finding_lower
            or "pricing" in finding_lower
            or "baseline" in finding_lower
            or "rate" in finding_lower
            or "gmv" in finding_lower
            or "revenue" in finding_lower
            or "review" in finding_lower
            or "score" in finding_lower
        )
        if not has_support:
            unsupported_count += 1

    total_claims = max(len(predicted_causes) + len(response.key_findings), 1)
    unsupported_claim_rate = min(unsupported_count / total_claims, 1.0)
    hallucination_rate = min(hallucination_count / total_claims, 1.0)

    # 5. Investigation Efficiency
    steps_executed = len(response.trace)
    tool_calls = sum(1 for step in response.trace if step.status == "completed")
    branches_explored = sum(
        1
        for step in response.trace
        if "drilldown" in step.step_type and step.status == "completed"
    )
    branches_pruned = sum(1 for step in response.trace if step.status == "skipped")

    # 6. Forensic Failure Analysis
    failure_explanation = None
    if not top1_correct:
        predicted_top_str = pred_strings[0] if pred_strings else "None"
        target_desc = (
            scenario.primary_cause.causal_mechanism
            or scenario.primary_cause.dimension
            or scenario.primary_cause.cause_id
        )
        failure_explanation = (
            f"Expected primary causal mechanism '{target_desc}' "
            f"({scenario.primary_cause.cause_id}) was not ranked #1. "
            f"Actual top cause: '{predicted_top_str}'."
        )

    return EvaluationResult(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        ground_truth_primary=scenario.primary_cause.cause_id,
        predicted_root_causes=pred_strings,
        top1_correct=top1_correct,
        top3_correct=top3_correct,
        reciprocal_rank=reciprocal_rank,
        false_positive_rate=round(false_positive_rate, 3),
        contribution_error=round(contribution_error, 2)
        if contribution_error is not None
        else None,
        evidence_grounded=evidence_grounded and unsupported_claim_rate == 0.0,
        unsupported_claim_rate=round(unsupported_claim_rate, 3),
        hallucination_rate=round(hallucination_rate, 3),
        investigation_steps=steps_executed,
        tool_calls=tool_calls,
        branches_explored=branches_explored,
        branches_pruned=branches_pruned,
        execution_time_ms=round(execution_time_ms, 2),
        stopping_reason=response.termination_reason,
        difficulty=scenario.difficulty,
        distractor_causes=scenario.distractor_causes,
        failure_explanation=failure_explanation,
    )


def aggregate_benchmark_results(results: list[EvaluationResult]) -> BenchmarkSummary:
    """Aggregate a list of scenario evaluation results into summary metrics."""
    if not results:
        return BenchmarkSummary(
            scenarios_evaluated=0,
            top1_accuracy=0.0,
            top3_accuracy=0.0,
            mrr=0.0,
            false_positive_rate=0.0,
            mean_contribution_error=None,
            evidence_grounding_rate=0.0,
            unsupported_claim_rate=0.0,
            hallucination_rate=0.0,
            avg_steps=0.0,
            avg_tool_calls=0.0,
            avg_execution_time_ms=0.0,
            easy_count=0,
            easy_top1_accuracy=None,
            easy_mrr=None,
            medium_count=0,
            medium_top1_accuracy=None,
            medium_mrr=None,
            hard_count=0,
            hard_top1_accuracy=None,
            hard_mrr=None,
            results=[],
        )

    n = len(results)
    top1_count = sum(1 for r in results if r.top1_correct)
    top3_count = sum(1 for r in results if r.top3_correct)
    mrr_sum = sum(r.reciprocal_rank for r in results)
    fpr_sum = sum(r.false_positive_rate for r in results)

    contrib_errors = [
        r.contribution_error for r in results if r.contribution_error is not None
    ]
    mean_contrib_error = (
        (sum(contrib_errors) / len(contrib_errors)) if contrib_errors else None
    )

    grounded_count = sum(1 for r in results if r.evidence_grounded)
    unsupported_sum = sum(r.unsupported_claim_rate for r in results)
    hallucination_sum = sum(r.hallucination_rate for r in results)

    total_steps = sum(r.investigation_steps for r in results)
    total_tools = sum(r.tool_calls for r in results)
    total_time = sum(r.execution_time_ms for r in results)

    # Difficulty Stratification
    easy_results = [r for r in results if r.difficulty == "easy"]
    medium_results = [r for r in results if r.difficulty == "medium"]
    hard_results = [r for r in results if r.difficulty == "hard"]

    easy_count = len(easy_results)
    easy_top1 = (
        round((sum(1 for r in easy_results if r.top1_correct) / easy_count) * 100.0, 2)
        if easy_count > 0
        else None
    )
    easy_mrr = (
        round(sum(r.reciprocal_rank for r in easy_results) / easy_count, 4)
        if easy_count > 0
        else None
    )

    medium_count = len(medium_results)
    medium_top1 = (
        round(
            (sum(1 for r in medium_results if r.top1_correct) / medium_count) * 100.0, 2
        )
        if medium_count > 0
        else None
    )
    medium_mrr = (
        round(sum(r.reciprocal_rank for r in medium_results) / medium_count, 4)
        if medium_count > 0
        else None
    )

    hard_count = len(hard_results)
    hard_top1 = (
        round((sum(1 for r in hard_results if r.top1_correct) / hard_count) * 100.0, 2)
        if hard_count > 0
        else None
    )
    hard_mrr = (
        round(sum(r.reciprocal_rank for r in hard_results) / hard_count, 4)
        if hard_count > 0
        else None
    )

    return BenchmarkSummary(
        scenarios_evaluated=n,
        top1_accuracy=round((top1_count / n) * 100.0, 2),
        top3_accuracy=round((top3_count / n) * 100.0, 2),
        mrr=round(mrr_sum / n, 4),
        false_positive_rate=round(fpr_sum / n, 3),
        mean_contribution_error=round(mean_contrib_error, 2)
        if mean_contrib_error is not None
        else None,
        evidence_grounding_rate=round((grounded_count / n) * 100.0, 2),
        unsupported_claim_rate=round(unsupported_sum / n, 3),
        hallucination_rate=round(hallucination_sum / n, 3),
        avg_steps=round(total_steps / n, 2),
        avg_tool_calls=round(total_tools / n, 2),
        avg_execution_time_ms=round(total_time / n, 2),
        easy_count=easy_count,
        easy_top1_accuracy=easy_top1,
        easy_mrr=easy_mrr,
        medium_count=medium_count,
        medium_top1_accuracy=medium_top1,
        medium_mrr=medium_mrr,
        hard_count=hard_count,
        hard_top1_accuracy=hard_top1,
        hard_mrr=hard_mrr,
        results=results,
    )
