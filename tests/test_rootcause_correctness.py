"""Regression and Correctness Tests for Root-Cause Reasoning & Invariants."""

from datetime import date

import pytest

from apps.ai.investigator import investigate_with_ai
from apps.analytics.agent import run_autonomous_investigation
from apps.analytics.agent.models import InvestigationAgentRequest
from apps.analytics.rootcause.engine import investigate_root_cause
from apps.analytics.rootcause.models import (
    RootCauseInvestigationRequest,
)
from apps.analytics.rootcause.scoring import decompose_volume_and_aov
from apps.api.db.connection import get_db_connection


def test_decomposition_volume_dominant_increase() -> None:
    """Test decomposition when volume surge dominates revenue increase."""
    # 100 orders -> 200 orders (+100%), AOV R$100 -> R$105 (+5%)
    decomp = decompose_volume_and_aov(
        observed_orders=200,
        baseline_orders=100,
        observed_aov=105.0,
        baseline_aov=100.0,
    )
    # Total change: 200*105 - 100*100 = 21000 - 10000 = 11000
    # Vol effect: (200 - 100) * 100 = 10000
    # AOV effect: (105 - 100) * 100 = 500
    # Interaction: 100 * 5 = 500
    assert decomp.total_change == 11000.0
    assert decomp.volume_effect == 10000.0
    assert decomp.aov_effect == 500.0
    assert decomp.interaction_effect == 500.0
    assert decomp.volume_contribution_pct is not None
    assert decomp.aov_contribution_pct is not None
    assert decomp.volume_contribution_pct > decomp.aov_contribution_pct
    assert decomp.volume_contribution_pct == pytest.approx(90.91, abs=0.1)


def test_decomposition_aov_dominant_increase() -> None:
    """Test decomposition when basket expansion dominates revenue increase."""
    # 100 orders -> 105 orders (+5%), AOV R$100 -> R$200 (+100%)
    decomp = decompose_volume_and_aov(
        observed_orders=105,
        baseline_orders=100,
        observed_aov=200.0,
        baseline_aov=100.0,
    )
    # Total change: 105*200 - 100*100 = 21000 - 10000 = 11000
    # Vol effect: (105 - 100) * 100 = 500
    # AOV effect: (200 - 100) * 100 = 10000
    # Interaction: 5 * 100 = 500
    assert decomp.total_change == 11000.0
    assert decomp.volume_effect == 500.0
    assert decomp.aov_effect == 10000.0
    assert decomp.aov_contribution_pct is not None
    assert decomp.volume_contribution_pct is not None
    assert decomp.aov_contribution_pct > decomp.volume_contribution_pct
    assert decomp.aov_contribution_pct == pytest.approx(90.91, abs=0.1)


def test_decomposition_volume_dominant_decrease() -> None:
    """Test decomposition when volume drop dominates revenue contraction."""
    # 200 orders -> 100 orders (-50%), AOV R$100 -> R$102 (+2%)
    decomp = decompose_volume_and_aov(
        observed_orders=100,
        baseline_orders=200,
        observed_aov=102.0,
        baseline_aov=100.0,
    )
    # Baseline GMV: 20000, Observed GMV: 10200, Total change: -9800
    # Vol effect: -100 * 100 = -10000
    # AOV effect: +2 * 200 = +400
    # Interaction: -100 * +2 = -200
    assert decomp.total_change == -9800.0
    assert decomp.volume_effect == -10000.0
    assert decomp.aov_effect == 400.0
    assert decomp.volume_contribution_pct is not None
    assert decomp.aov_contribution_pct is not None
    # Vol contribution is negative and dominant in magnitude
    assert abs(decomp.volume_contribution_pct) > abs(decomp.aov_contribution_pct)


def test_decomposition_aov_dominant_decrease() -> None:
    """Test decomposition when basket size drop dominates revenue contraction."""
    # 100 orders -> 98 orders (-2%), AOV R$200 -> R$100 (-50%)
    decomp = decompose_volume_and_aov(
        observed_orders=98,
        baseline_orders=100,
        observed_aov=100.0,
        baseline_aov=200.0,
    )
    # Baseline GMV: 20000, Observed GMV: 9800, Total change: -10200
    # Vol effect: -2 * 200 = -400
    # AOV effect: -100 * 100 = -10000
    # Interaction: -2 * -100 = +200
    assert decomp.total_change == -10200.0
    assert decomp.volume_effect == -400.0
    assert decomp.aov_effect == -10000.0
    assert decomp.aov_contribution_pct is not None
    assert decomp.volume_contribution_pct is not None
    assert abs(decomp.aov_contribution_pct) > abs(decomp.volume_contribution_pct)


def test_different_anomaly_dates_produce_different_root_causes() -> None:
    """Verify that different dates yield mathematically different root causes."""
    with get_db_connection() as conn:
        # Date 1: 2017-11-16 (Volume surge dominant)
        req_16 = InvestigationAgentRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 16),
            comparison_days=7,
        )
        resp_16 = run_autonomous_investigation(conn, req_16)

        # Date 2: 2017-11-20 (AOV expansion dominant)
        req_20 = InvestigationAgentRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 20),
            comparison_days=7,
        )
        resp_20 = run_autonomous_investigation(conn, req_20)

        # Top cause for 16 Nov must be volume surge
        assert len(resp_16.top_root_causes) > 0
        top_16 = resp_16.top_root_causes[0]
        assert top_16.causal_mechanism == "order_volume"
        assert "Order Volume" in top_16.title

        # Top cause for 20 Nov must be AOV expansion
        assert len(resp_20.top_root_causes) > 0
        top_20 = resp_20.top_root_causes[0]
        assert top_20.causal_mechanism == "average_order_value"
        assert "Average Order Value" in top_20.title

        # Different dates produce different primary causes
        assert top_16.causal_mechanism != top_20.causal_mechanism


def test_no_contradictory_natural_language_explanation_on_aov_increase() -> None:
    """Test that when AOV increases, narrative does not say 'lower order value'."""
    with get_db_connection() as conn:
        req = RootCauseInvestigationRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 20),
            comparison_days=7,
        )
        rc_resp = investigate_root_cause(conn, req)
        assert rc_resp.decomposition is not None
        assert rc_resp.decomposition.observed_aov > rc_resp.decomposition.baseline_aov

        ai_resp = investigate_with_ai(rc_resp)

        # Contradiction check
        for finding in ai_resp.key_findings:
            if "Average Order Value" in finding or "AOV" in finding:
                assert "lower" not in finding.lower()
                assert "contraction" not in finding.lower()
                assert "primary driver" in finding.lower()

        # Business interpretation check
        for interp in ai_resp.business_interpretation:
            assert "basket size contraction" not in interp.lower()


def test_scn002_volume_contraction_ranking_on_2017_11_19() -> None:
    """Verify SCN-002 volume contraction is ranked #1 on actual date."""
    with get_db_connection() as conn:
        req = InvestigationAgentRequest(
            metric="total_gmv",
            anomaly_date=date(2017, 11, 19),
            comparison_days=7,
            dimensions=["product_category", "customer_state", "seller"],
        )
        resp = run_autonomous_investigation(conn, req)

        assert resp.anomaly_summary.direction == "decrease"
        assert resp.decomposition is not None
        assert abs(resp.decomposition.volume_contribution_pct or 0.0) > 70.0

        assert len(resp.top_root_causes) >= 2
        top1 = resp.top_root_causes[0]
        assert top1.rank == 1
        assert top1.causal_mechanism == "order_volume"
        assert top1.causal_category == "macro_driver"
        assert "Order Volume" in top1.title

        top2 = resp.top_root_causes[1]
        assert top2.rank == 2
        assert top2.causal_mechanism == "average_order_value"
