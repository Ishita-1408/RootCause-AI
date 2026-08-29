"""Phase H — Hallucination Remediation & Firewall Regression Tests."""

from datetime import date

from apps.analytics.agent.agent import AutonomousInvestigationAgent
from apps.analytics.agent.claims import generate_evidence_backed_claims
from apps.analytics.agent.firewall import apply_claim_firewall
from apps.analytics.agent.models import (
    EvidenceBackedClaim,
    InvestigationAgentRequest,
    RankedRootCause,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    VolumeValueDecomposition,
)
from apps.api.db.connection import get_db_connection
from evaluation.hallucination.extractor import (
    extract_claims_from_response,
    extract_evidence_from_response,
)
from evaluation.hallucination.verifier import verify_single_claim


def test_agent_emits_zero_hallucinations_on_canonical_scenarios() -> None:
    """Verify that agent produces 0 unsupported or contradicted claims."""
    from evaluation.scenarios import get_all_scenarios

    scenarios = get_all_scenarios()[:6]
    with get_db_connection() as conn:
        agent = AutonomousInvestigationAgent(conn=conn)

        for scn in scenarios:
            req = InvestigationAgentRequest(
                metric=scn.target_metric,
                anomaly_date=scn.anomaly_date,
                comparison_days=scn.comparison_days,
                dimensions=["product_category", "customer_state", "seller"],
            )
            resp = agent.run_investigation(req)
            claims = extract_claims_from_response(resp)
            evidence = extract_evidence_from_response(resp)

            assert len(claims) >= 6, f"Expected >= 6 claims for {scn.scenario_id}"
            for c in claims:
                res = verify_single_claim(c, evidence, scenario_date=scn.anomaly_date)
                assert res.verification_status == "SUPPORTED", (
                    f"Scenario {scn.scenario_id} claim {c.claim_id} failed: "
                    f"{res.failure_reason}"
                )


def test_firewall_blocks_fabricated_percentage() -> None:
    """Verify that the claim firewall blocks fabricated percentage values."""
    anom_date = date(2017, 11, 24)
    fake_claim = EvidenceBackedClaim(
        evidence_id="ev_decomp_vol_2017-11-24",
        claim_type="numerical",
        subject="Order volume shifted +999.0% vs 7-day rolling baseline.",
        metric="orders_count",
        value=999.0,  # Fabricated percentage
        percentage_change=999.0,
        dimension="order_volume",
        dimension_value="volume",
        derived_formula="percentage_change",
    )

    with get_db_connection() as conn:
        agent = AutonomousInvestigationAgent(conn=conn)
        resp = agent.run_investigation(
            InvestigationAgentRequest(
                metric="total_gmv",
                anomaly_date=anom_date,
                comparison_days=7,
            )
        )
        pool = extract_evidence_from_response(resp)
        verified, findings = apply_claim_firewall(
            claims=[fake_claim],
            evidence_pool=pool,
            scenario_date=anom_date,
        )

        assert len(verified) == 0, "Fabricated claim must be blocked by firewall"
        assert findings == ["Insufficient evidence to support this conclusion."]


def test_firewall_blocks_reversed_sign_contradiction() -> None:
    """Verify that the claim firewall blocks sign inversions."""
    anom_date = date(2017, 11, 19)
    inverted_claim = EvidenceBackedClaim(
        evidence_id="ev_decomp_vol_2017-11-19",
        claim_type="numerical",
        subject="Order volume shifted +76.5% vs 7-day rolling baseline.",
        metric="orders_count",
        value=76.5,  # Real shift is negative (-16.8%)
        percentage_change=76.5,
        direction="increase",  # Real direction is decrease
        dimension="order_volume",
        dimension_value="volume",
        derived_formula="percentage_change",
    )

    with get_db_connection() as conn:
        agent = AutonomousInvestigationAgent(conn=conn)
        resp = agent.run_investigation(
            InvestigationAgentRequest(
                metric="total_gmv",
                anomaly_date=anom_date,
                comparison_days=7,
            )
        )
        pool = extract_evidence_from_response(resp)
        verified, _ = apply_claim_firewall(
            claims=[inverted_claim],
            evidence_pool=pool,
            scenario_date=anom_date,
        )

        assert len(verified) == 0, "Inverted sign claim must be blocked by firewall"


def test_firewall_blocks_unsupported_causal_explanation() -> None:
    """Verify that the claim firewall blocks unsupported causal mechanisms."""
    anom_date = date(2017, 11, 24)
    fake_causal_claim = EvidenceBackedClaim(
        evidence_id="ev_decomp_vol_2017-11-24",
        claim_type="causal",
        subject="AOV drove the Black Friday revenue surge.",
        metric="orders_count",
        causal_mechanism="average_order_value",
        # Real dominant mechanism is order_volume
        derived_formula=None,
    )

    with get_db_connection() as conn:
        agent = AutonomousInvestigationAgent(conn=conn)
        resp = agent.run_investigation(
            InvestigationAgentRequest(
                metric="total_gmv",
                anomaly_date=anom_date,
                comparison_days=7,
            )
        )
        pool = extract_evidence_from_response(resp)
        verified, _ = apply_claim_firewall(
            claims=[fake_causal_claim],
            evidence_pool=pool,
            scenario_date=anom_date,
        )

        assert len(verified) == 0, "Fake causal mechanism must be blocked by firewall"


def test_claims_generator_accuracy_and_invariants() -> None:
    """Verify that generate_evidence_backed_claims preserves exact math."""
    summary = AnomalySummary(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        baseline_start_date=date(2017, 11, 17),
        baseline_end_date=date(2017, 11, 23),
        observed_value=152653.74,
        baseline_value=31524.93,
        absolute_change=121128.81,
        percentage_change=384.23,
        direction="increase",
    )
    decomp = VolumeValueDecomposition(
        observed_orders=1176.0,
        baseline_orders=206.57,
        observed_aov=129.81,
        baseline_aov=152.61,
        volume_effect=121000.0,
        aov_effect=-26815.0,
        interaction_effect=26943.81,
        total_change=121128.81,
        volume_contribution_pct=99.89,
        aov_contribution_pct=-22.14,
        interaction_contribution_pct=22.25,
    )
    ops = OperationalIndicators(
        observed_late_delivery_rate=40.14,
        baseline_late_delivery_rate=14.25,
        late_delivery_rate_change=25.89,
        observed_avg_delivery_days=17.2,
        baseline_avg_delivery_days=14.14,
        avg_delivery_days_change=3.06,
        observed_cancellation_rate=0.0,
        baseline_cancellation_rate=0.55,
        cancellation_rate_change=-0.55,
        observed_avg_review_score=3.73,
        baseline_avg_review_score=3.94,
        avg_review_score_change=-0.21,
    )
    contrib = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=58410.20,
            baseline_value=12400.00,
            absolute_change=46010.20,
            percentage_change=271.05,
            contribution_pct=37.98,
            direction="increase",
            rank=1,
        )
    ]
    rc = [
        RankedRootCause(
            rank=1,
            title="Order Volume Surge",
            dimension="order_volume",
            dimension_value="1,176 orders (vs 207)",
            contribution_pct=99.9,
            absolute_change=121000.0,
            score=150.0,
            explanation="Volume surge driven by Black Friday",
            causal_category="macro_driver",
            causal_mechanism="order_volume",
        )
    ]

    claims = generate_evidence_backed_claims(
        summary=summary,
        decomposition=decomp,
        operational_signals=ops,
        contributors=contrib,
        top_root_causes=rc,
    )

    assert len(claims) >= 5
    # Order volume shift check
    vol_claim = next(c for c in claims if c.evidence_id == "ev_decomp_vol_2017-11-24")
    assert vol_claim.value is not None
    assert round(vol_claim.value, 1) == 469.3
    assert vol_claim.baseline_value == 206.57
