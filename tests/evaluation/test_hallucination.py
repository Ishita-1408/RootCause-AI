"""Adversarial Hallucination Evaluation Test Suite for Phase G.

Covers all 16 mandatory adversarial failure modes:
1. Correct claim + correct evidence
2. Correct root cause + fabricated percentage
3. Correct root cause + fabricated currency value
4. Correct metric + wrong value
5. Correct value + wrong metric
6. Correct metric + wrong date
7. Correct metric + wrong dimension
8. Correct dimension + wrong dimension value
9. Correct direction + fabricated magnitude
10. Opposite direction
11. Unsupported causal explanation
12. Evidence from another scenario
13. Missing evidence ID
14. Incorrect derived percentage
15. Correct evidence but incorrect conclusion
16. Contradictory claim
"""

from datetime import date

import pytest

from evaluation.hallucination.models import (
    EvidenceRecord,
    StructuredClaim,
)
from evaluation.hallucination.verifier import (
    evaluate_claims_against_evidence,
    verify_single_claim,
)


@pytest.fixture
def canonical_evidence_pool() -> list[EvidenceRecord]:
    """Standard empirical evidence pool for Black Friday 2017-11-24."""
    anom_date = date(2017, 11, 24)
    return [
        EvidenceRecord(
            evidence_id="ev_gmv_bf2017",
            source="mart_daily_kpis",
            metric="total_gmv",
            observed_value=152653.74,
            baseline_value=31524.93,
            delta=121128.81,
            delta_pct=384.23,
            direction="increase",
            dimension=None,
            dimension_value=None,
            anomaly_date=anom_date,
            comparison_window=7,
            query_tool_id="fetch_date_metrics",
            raw_details={},
        ),
        EvidenceRecord(
            evidence_id="ev_orders_bf2017",
            source="decomposition_engine",
            metric="orders_count",
            observed_value=1176.0,
            baseline_value=206.57,
            delta=969.43,
            delta_pct=469.30,
            direction="increase",
            dimension="order_volume",
            dimension_value="volume",
            anomaly_date=anom_date,
            comparison_window=7,
            query_tool_id="decompose_volume_and_aov",
            raw_details={
                "volume_effect": 121000.0,
                "volume_contribution_pct": 89.5,
                "dominant_mechanism": "order_volume",
            },
        ),
        EvidenceRecord(
            evidence_id="ev_aov_bf2017",
            source="decomposition_engine",
            metric="average_order_value",
            observed_value=129.81,
            baseline_value=152.61,
            delta=-22.80,
            delta_pct=-14.94,
            direction="decrease",
            dimension="average_order_value",
            dimension_value="aov",
            anomaly_date=anom_date,
            comparison_window=7,
            query_tool_id="decompose_volume_and_aov",
            raw_details={
                "aov_effect": -15000.0,
                "aov_contribution_pct": -10.5,
                "dominant_mechanism": "order_volume",
            },
        ),
        EvidenceRecord(
            evidence_id="ev_sp_slice_bf2017",
            source="contribution_analyzer",
            metric="total_gmv",
            observed_value=58410.20,
            baseline_value=12400.00,
            delta=46010.20,
            delta_pct=271.05,
            direction="increase",
            dimension="customer_state",
            dimension_value="SP",
            anomaly_date=anom_date,
            comparison_window=7,
            query_tool_id="analyze_dimension_breakdown",
            raw_details={
                "contribution_pct": 37.98,
                "rank": 1,
            },
        ),
    ]


# Case 1: Correct claim + correct evidence
def test_case_01_correct_claim_and_evidence(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify supported status when claim matches empirical evidence."""
    claim = StructuredClaim(
        claim_id="clm_01",
        claim_type="numerical",
        metric="orders_count",
        subject="Orders increased by 469.3% on Black Friday",
        value=469.30,
        unit="pct",
        direction="increase",
        dimension="order_volume",
        dimension_value="volume",
        anomaly_date=date(2017, 11, 24),
        comparison_window=7,
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "SUPPORTED"
    assert res.absolute_error == pytest.approx(0.0, abs=0.1)


# Case 2: Correct root cause + fabricated percentage
def test_case_02_fabricated_percentage(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when root cause is correct but percentage is fabricated."""
    claim = StructuredClaim(
        claim_id="clm_02",
        claim_type="causal",
        metric="orders_count",
        subject="Order volume surged 950.0%",
        value=950.0,  # Real value is 469.3%
        unit="pct",
        direction="increase",
        dimension="order_volume",
        dimension_value="volume",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Fabricated / Incorrect number" in (res.failure_reason or "")


# Case 3: Correct root cause + fabricated currency value
def test_case_03_fabricated_currency_value(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when GMV value is fabricated."""
    claim = StructuredClaim(
        claim_id="clm_03",
        claim_type="numerical",
        metric="total_gmv",
        subject="Observed GMV was R$ 450,000.00",
        value=450000.00,  # Real value is R$ 152,653.74
        unit="BRL",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_gmv_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Fabricated / Incorrect number" in (res.failure_reason or "")


# Case 4: Correct metric + wrong value
def test_case_04_wrong_metric_value(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when metric is correct but value is completely wrong."""
    claim = StructuredClaim(
        claim_id="clm_04",
        claim_type="numerical",
        metric="average_order_value",
        subject="AOV was R$ 350.00",
        value=350.00,  # Real value is 129.81
        unit="BRL",
        direction="decrease",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_aov_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


# Case 5: Correct value + wrong metric
def test_case_05_correct_value_wrong_metric(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when value is assigned to wrong metric."""
    # 152653.74 is total_gmv, but claimed as orders_count
    claim = StructuredClaim(
        claim_id="clm_05",
        claim_type="numerical",
        metric="orders_count",
        subject="Total orders were 152,653.74",
        value=152653.74,
        unit="orders",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


# Case 6: Correct metric + wrong date
def test_case_06_wrong_date(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when claim refers to another date."""
    claim = StructuredClaim(
        claim_id="clm_06",
        claim_type="numerical",
        metric="total_gmv",
        subject="GMV on 2017-12-25",
        value=152653.74,
        anomaly_date=date(2017, 12, 25),  # Pool only has 2017-11-24
        evidence_ids=["ev_gmv_bf2017"],
    )
    res = verify_single_claim(
        claim, canonical_evidence_pool, scenario_date=date(2017, 12, 25)
    )
    assert res.verification_status == "CONTRADICTED"
    assert "date mismatch" in (res.failure_reason or "").lower()


# Case 7: Correct metric + wrong dimension
def test_case_07_wrong_dimension(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when dimension is misattributed."""
    claim = StructuredClaim(
        claim_id="clm_07",
        claim_type="segment",
        metric="total_gmv",
        subject="Product category contributed 37.98%",
        value=37.98,
        dimension="product_category",  # Evidence is customer_state
        dimension_value="SP",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        derived_formula="contribution_percentage",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Dimension mismatch" in (res.failure_reason or "")


# Case 8: Correct dimension + wrong dimension value
def test_case_08_wrong_dimension_value(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when dimension slice value is wrong."""
    claim = StructuredClaim(
        claim_id="clm_08",
        claim_type="segment",
        metric="total_gmv",
        subject="Rio de Janeiro contributed 37.98%",
        value=37.98,
        dimension="customer_state",
        dimension_value="RJ",  # Evidence is for SP
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        derived_formula="contribution_percentage",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Dimension value mismatch" in (res.failure_reason or "")


# Case 9: Correct direction + fabricated magnitude
def test_case_09_fabricated_magnitude(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when direction is correct (increase) but magnitude is 10x."""
    claim = StructuredClaim(
        claim_id="clm_09",
        claim_type="numerical",
        metric="total_gmv",
        subject="GMV grew by 3800%",
        value=3800.0,  # Real delta_pct is 384.23%
        unit="pct",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_gmv_bf2017"],
        derived_formula="percentage_change",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


# Case 10: Opposite direction
def test_case_10_opposite_direction(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when claim claims contraction but evidence is expansion."""
    claim = StructuredClaim(
        claim_id="clm_10",
        claim_type="trend",
        metric="orders_count",
        subject="Orders declined significantly",
        direction="decrease",  # Evidence is increase (+469%)
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Directional contradiction" in (res.failure_reason or "")


# Case 11: Unsupported causal explanation
def test_case_11_unsupported_causal_explanation(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when causal mechanism contradicts decomposition."""
    claim = StructuredClaim(
        claim_id="clm_11",
        claim_type="causal",
        metric="orders_count",
        subject="Average Order Value expansion drove the revenue spike",
        causal_mechanism="average_order_value",
        # Decomposition proves order_volume drove 89.5%
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Causal contradiction" in (res.failure_reason or "")


# Case 12: Evidence from another scenario
def test_case_12_evidence_from_another_scenario(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify cross-scenario evidence injection detection."""
    # Alien evidence record from 2017-09-01
    alien_evidence = EvidenceRecord(
        evidence_id="ev_alien_sep01",
        source="mart_daily_kpis",
        metric="total_gmv",
        observed_value=25000.0,
        baseline_value=20000.0,
        delta=5000.0,
        delta_pct=25.0,
        direction="increase",
        anomaly_date=date(2017, 9, 1),
        comparison_window=7,
    )
    pool = canonical_evidence_pool + [alien_evidence]

    claim = StructuredClaim(
        claim_id="clm_12",
        claim_type="numerical",
        metric="total_gmv",
        subject="Revenue was R$ 25,000 on Black Friday",
        value=25000.0,
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_alien_sep01"],
    )
    res = verify_single_claim(claim, pool, scenario_date=date(2017, 11, 24))
    assert res.verification_status == "CONTRADICTED"
    assert "date mismatch" in (res.failure_reason or "").lower()


# Case 13: Missing evidence ID
def test_case_13_missing_evidence_id(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify handling when claim points to non-existent evidence ID."""
    claim = StructuredClaim(
        claim_id="clm_13",
        claim_type="numerical",
        metric="non_existent_metric",
        subject="Fraud rate jumped",
        value=99.9,
        evidence_ids=["ev_non_existent_id_12345"],
        anomaly_date=date(2017, 11, 24),
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "No supporting evidence found" in (res.failure_reason or "")


# Case 14: Incorrect derived percentage
def test_case_14_incorrect_derived_percentage(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify mathematical recalculation rejects incorrect derived percentage."""
    # Ground truth (1176 - 206.57)/206.57 * 100 = 469.30%
    claim = StructuredClaim(
        claim_id="clm_14",
        claim_type="numerical",
        metric="orders_count",
        subject="Orders increased by 125%",
        value=125.0,  # Derived calculation is 469.3%
        unit="pct",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


# Case 15: Correct evidence but incorrect conclusion
def test_case_15_correct_evidence_incorrect_conclusion(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify detection when conclusion inverts evidence trend."""
    claim = StructuredClaim(
        claim_id="clm_15",
        claim_type="trend",
        metric="average_order_value",
        subject="Average order value expanded significantly",
        direction="increase",  # Real direction is decrease
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_aov_bf2017"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


# Case 16: Contradictory claim
def test_case_16_contradictory_claim(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify sign contradiction detection."""
    claim = StructuredClaim(
        claim_id="clm_16",
        claim_type="numerical",
        metric="average_order_value",
        subject="AOV changed by +R$ 22.80",
        value=22.80,  # Real delta is -22.80
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_aov_bf2017"],
        derived_formula="absolute_change",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "CONTRADICTED"


def test_batch_claim_evaluation_metrics(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Test full aggregate batch evaluation metrics calculation."""
    c_valid = StructuredClaim(
        claim_id="c_valid",
        claim_type="numerical",
        metric="orders_count",
        subject="Valid orders",
        value=469.30,
        unit="pct",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )
    c_fabricated = StructuredClaim(
        claim_id="c_fab",
        claim_type="numerical",
        metric="orders_count",
        subject="Fake orders",
        value=9999.0,
        unit="pct",
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )

    summary = evaluate_claims_against_evidence(
        claims=[c_valid, c_fabricated],
        evidence_pool=canonical_evidence_pool,
        scenario_date=date(2017, 11, 24),
    )

    assert summary.total_claims == 2
    assert summary.supported_count == 1
    assert summary.contradicted_count == 1
    assert summary.claim_grounding_rate == 50.0
    assert summary.hallucination_rate == 50.0
    assert summary.contradiction_rate == 50.0


# Case 17: Converting association/concentration into causal assertion (Phase K)
def test_case_17_unsupported_causal_language_assertion(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that 'X caused Y' claims without identification are rejected."""
    claim = StructuredClaim(
        claim_id="clm_17",
        claim_type="causal",
        metric="total_gmv",
        subject="São Paulo caused the revenue increase.",
        value=37.98,
        direction="increase",
        dimension="customer_state",
        dimension_value="SP",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        derived_formula="contribution_percentage",
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "Unsupported causal language" in (res.failure_reason or "")


# Case 18: Inferring causality from statistical significance alone (Phase K)
def test_case_18_inferring_causality_from_statistical_significance(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claims asserting 'proves causality' are rejected."""
    claim = StructuredClaim(
        claim_id="clm_18",
        claim_type="causal",
        metric="orders_count",
        subject="Significant volume shift proves causality.",
        value=469.30,
        direction="increase",
        dimension="order_volume",
        dimension_value="volume",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "Unsupported causal language" in (res.failure_reason or "")


# Case 19: Inferring sole responsibility from concentration alone (Phase K)
def test_case_19_inferring_causality_from_concentration_alone(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that 'is responsible for' is rejected under observational levels."""
    claim = StructuredClaim(
        claim_id="clm_19",
        claim_type="causal",
        metric="total_gmv",
        subject="SP is responsible for the drop in regional performance.",
        value=37.98,
        direction="decrease",
        dimension="customer_state",
        dimension_value="SP",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "Unsupported causal language" in (res.failure_reason or "")


# Case 20: Allowed compliant associational/mechanistic phrasing (Phase K)
def test_case_20_allowed_associational_and_mechanistic_language(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that compliant phrasing ('is concentrated in') is supported."""
    claim = StructuredClaim(
        claim_id="clm_20",
        claim_type="segment",
        metric="total_gmv",
        subject="Growth is concentrated in SP (+37.98% share).",
        value=37.98,
        direction="increase",
        dimension="customer_state",
        dimension_value="SP",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        derived_formula="contribution_percentage",
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "SUPPORTED"
    assert res.failure_reason is None


# Case 21: Non-significant result described as statistically significant (Phase K)
def test_case_21_non_significant_result_claimed_as_significant(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claims with p > 0.05 claiming significance are rejected."""
    claim = StructuredClaim(
        claim_id="clm_21",
        claim_type="trend",
        metric="total_gmv",
        subject="Statistically significant shift observed in baseline comparison.",
        value=150000.0,
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_kpi_total_gmv_2017-11-24"],
        p_value=0.235,
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "p-value" in (res.failure_reason or "")


# Case 22: Confidence interval crossing zero claimed as significant shift (Phase K)
def test_case_22_confidence_interval_crossing_zero(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claims with CI crossing zero claiming significance are rejected."""
    claim = StructuredClaim(
        claim_id="clm_22",
        claim_type="trend",
        metric="total_gmv",
        subject="Statistically significant difference detected in GMV.",
        value=150000.0,
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_kpi_total_gmv_2017-11-24"],
        p_value=0.04,
        confidence_interval=[-12.5, 45.0],
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "confidence interval" in (res.failure_reason or "")


# Case 23: Very small sample size claimed as significant inference (Phase K)
def test_case_23_small_sample_size_inference(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claims asserting significance with n < 2 are rejected."""
    claim = StructuredClaim(
        claim_id="clm_23",
        claim_type="trend",
        metric="total_gmv",
        subject="Statistically significant shift detected in single observation.",
        value=150000.0,
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_kpi_total_gmv_2017-11-24"],
        sample_size=1,
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "sample size" in (res.failure_reason or "")


# Case 24: Negative effect incorrectly described as positive (Phase K)
def test_case_24_negative_effect_described_as_positive(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that inverted direction claims are contradicted."""
    claim = StructuredClaim(
        claim_id="clm_24",
        claim_type="numerical",
        metric="orders_count",
        subject="Order volume increased sharply.",
        value=100.0,
        direction="increase",
        dimension="order_volume",
        dimension_value="volume",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_orders_bf2017"],
        derived_formula="percentage_change",
    )
    # Mutate matching evidence to decrease
    pool = [
        e.model_copy(update={"direction": "decrease"}) for e in canonical_evidence_pool
    ]
    res = verify_single_claim(claim, pool)
    assert res.verification_status == "CONTRADICTED"
    assert "Directional contradiction" in (res.failure_reason or "")


# Case 25: Practical significance negligible despite statistical claim (Phase K)
def test_case_25_negligible_practical_significance(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claiming primary driver for negligible effect is rejected."""
    claim = StructuredClaim(
        claim_id="clm_25",
        claim_type="causal",
        metric="total_gmv",
        subject="Primary driver explaining regional variance.",
        value=37.98,
        direction="increase",
        dimension="customer_state",
        dimension_value="SP",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_sp_slice_bf2017"],
        effect_size=0.002,
        causal_support_level="associational",
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "Practical significance failure" in (res.failure_reason or "")


# Case 26: Missing statistical evidence (Phase K)
def test_case_26_missing_statistical_evidence(
    canonical_evidence_pool: list[EvidenceRecord],
) -> None:
    """Verify that claims with nonexistent evidence IDs fail verification."""
    claim = StructuredClaim(
        claim_id="clm_26",
        claim_type="numerical",
        metric="unrecorded_experimental_metric",
        subject="Revenue grew 50% according to unrecorded test.",
        value=50.0,
        direction="increase",
        anomaly_date=date(2017, 11, 24),
        evidence_ids=["ev_nonexistent_table_query"],
    )
    res = verify_single_claim(claim, canonical_evidence_pool)
    assert res.verification_status == "UNSUPPORTED"
    assert "No supporting evidence found" in (res.failure_reason or "")
