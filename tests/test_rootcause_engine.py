"""Unit and integration tests for Phase 5B Root-Cause Drill-Down Engine."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from apps.analytics.rootcause.engine import investigate_root_cause
from apps.analytics.rootcause.models import (
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
)
from apps.analytics.rootcause.scoring import (
    calculate_slice_contributors,
    decompose_volume_and_aov,
)


# 1. Test Baseline Percentage Change and Calculations
def test_percentage_change_calculation() -> None:
    """Test percentage change calculations across growth, decline, and zero baseline."""
    slices = [
        {"slice_value": "Category_A", "observed_value": 150.0, "baseline_value": 100.0},
        {"slice_value": "Category_B", "observed_value": 50.0, "baseline_value": 100.0},
        {"slice_value": "Category_C", "observed_value": 100.0, "baseline_value": 0.0},
        {"slice_value": "Category_D", "observed_value": 0.0, "baseline_value": 0.0},
    ]

    contribs = calculate_slice_contributors(
        slices=slices,  # type: ignore[arg-type]
        dimension_name="product_category",
        total_metric_change=100.0,
    )

    # Category_A: +50 (+50.0%)
    cat_a = next(c for c in contribs if c.dimension_value == "Category_A")
    assert cat_a.absolute_change == 50.0
    assert cat_a.percentage_change == 50.0
    assert cat_a.direction == "increase"
    assert cat_a.contribution_pct == 50.0

    # Category_B: -50 (-50.0%)
    cat_b = next(c for c in contribs if c.dimension_value == "Category_B")
    assert cat_b.absolute_change == -50.0
    assert cat_b.percentage_change == -50.0
    assert cat_b.direction == "decrease"
    assert cat_b.contribution_pct == -50.0

    # Category_C: +100 (Zero baseline -> 100%)
    cat_c = next(c for c in contribs if c.dimension_value == "Category_C")
    assert cat_c.absolute_change == 100.0
    assert cat_c.percentage_change == 100.0

    # Category_D: 0.0 (Zero baseline and zero observed -> 0%)
    cat_d = next(c for c in contribs if c.dimension_value == "Category_D")
    assert cat_d.absolute_change == 0.0
    assert cat_d.percentage_change == 0.0
    assert cat_d.direction == "unchanged"


# 2. Test Volume vs. AOV Decomposition Mathematical Identity
def test_volume_aov_decomposition_identity() -> None:
    """Verify that volume_effect + aov_effect + interaction_effect == total_change."""
    obs_orders = 1200.0
    base_orders = 1000.0
    obs_aov = 150.0
    base_aov = 120.0

    decomp = decompose_volume_and_aov(
        observed_orders=obs_orders,
        baseline_orders=base_orders,
        observed_aov=obs_aov,
        baseline_aov=base_aov,
    )

    expected_gmv_obs = obs_orders * obs_aov  # 180,000
    expected_gmv_base = base_orders * base_aov  # 120,000
    expected_delta_gmv = expected_gmv_obs - expected_gmv_base  # 60,000

    assert (
        decomp.volume_effect + decomp.aov_effect + decomp.interaction_effect
        == expected_delta_gmv
    )
    assert decomp.total_change == expected_delta_gmv

    # Volume effect: (1200 - 1000) * 120 = 24,000
    assert decomp.volume_effect == 24000.0
    # AOV effect: (150 - 120) * 1000 = 30,000
    assert decomp.aov_effect == 30000.0
    # Interaction: 200 * 30 = 6,000
    assert decomp.interaction_effect == 6000.0


# 3. Test Zero Total Change Handling
def test_zero_total_change_contribution() -> None:
    """Test that zero total change returns None for contribution_pct safely."""
    slices = [
        {"slice_value": "SP", "observed_value": 100.0, "baseline_value": 50.0},
        {"slice_value": "RJ", "observed_value": 50.0, "baseline_value": 100.0},
    ]

    contribs = calculate_slice_contributors(
        slices=slices,  # type: ignore[arg-type]
        dimension_name="customer_state",
        total_metric_change=0.0,
    )

    assert contribs[0].contribution_pct is None
    assert contribs[1].contribution_pct is None


# 4. Test Ranking Logic
def test_contributor_ranking_by_absolute_magnitude() -> None:
    """Test that slice contributors are ranked by absolute magnitude descending."""
    slices = [
        {
            "slice_value": "Cat_Small",
            "observed_value": 10.0,
            "baseline_value": 0.0,
        },  # +10
        {
            "slice_value": "Cat_Large_Drop",
            "observed_value": 0.0,
            "baseline_value": 100.0,
        },  # -100
        {
            "slice_value": "Cat_Medium_Gain",
            "observed_value": 50.0,
            "baseline_value": 0.0,
        },  # +50
    ]

    contribs = calculate_slice_contributors(
        slices=slices,  # type: ignore[arg-type]
        dimension_name="product_category",
        total_metric_change=-40.0,
    )

    assert len(contribs) == 3
    assert contribs[0].dimension_value == "Cat_Large_Drop"
    assert contribs[0].rank == 1
    assert contribs[1].dimension_value == "Cat_Medium_Gain"
    assert contribs[1].rank == 2
    assert contribs[2].dimension_value == "Cat_Small"
    assert contribs[2].rank == 3


# 5. Test Input Validation (Invalid Metrics & Dimensions)
def test_invalid_metric_rejection() -> None:
    """Test that unapproved metrics are rejected."""
    with pytest.raises(ValueError, match="Unsupported metric"):
        RootCauseInvestigationRequest(
            metric="unsupported_kpi",
            anomaly_date=date(2018, 6, 15),
        )


def test_invalid_dimension_rejection() -> None:
    """Test that unapproved dimensions are rejected."""
    with pytest.raises(ValueError, match="Invalid dimensions"):
        RootCauseInvestigationRequest(
            metric="total_gmv",
            anomaly_date=date(2018, 6, 15),
            dimensions=["invalid_dimension"],
        )


# 6. Test Mocked Root Cause Investigation Orchestration & No-Lookahead
@patch("apps.analytics.rootcause.engine.fetch_dimension_slices")
@patch("apps.analytics.rootcause.engine.fetch_baseline_daily_metrics")
@patch("apps.analytics.rootcause.engine.fetch_date_metrics")
def test_investigate_root_cause_orchestration_mocked(
    mock_fetch_date: MagicMock,
    mock_fetch_baseline: MagicMock,
    mock_fetch_slices: MagicMock,
) -> None:
    """Test end-to-end investigation orchestration with mock data."""
    mock_conn = MagicMock()

    mock_fetch_date.return_value = {
        "orders_count": 500.0,
        "total_gmv": 50000.0,
        "average_order_value": 100.0,
        "late_delivery_rate": 15.0,
        "avg_delivery_days": 14.0,
        "cancellation_rate": 0.5,
        "avg_review_score": 3.8,
    }

    mock_fetch_baseline.return_value = {
        "orders_count": 1000.0,
        "total_gmv": 120000.0,
        "average_order_value": 120.0,
        "late_delivery_rate": 8.0,
        "avg_delivery_days": 10.0,
        "cancellation_rate": 0.2,
        "avg_review_score": 4.2,
    }

    mock_fetch_slices.return_value = [
        {
            "slice_value": "office_furniture",
            "observed_value": 10000.0,
            "baseline_value": 40000.0,
        },
    ]

    req = RootCauseInvestigationRequest(
        metric="total_gmv",
        anomaly_date=date(2018, 6, 15),
        comparison_days=7,
        dimensions=["product_category", "customer_state"],
    )

    resp = investigate_root_cause(conn=mock_conn, request=req)

    assert isinstance(resp, RootCauseInvestigationResponse)
    # Check baseline period dates: 7 days prior ending 2018-06-14 (strict no-lookahead)
    assert resp.summary.baseline_end_date == date(2018, 6, 14)
    assert resp.summary.baseline_start_date == date(2018, 6, 8)
    assert resp.summary.observed_value == 50000.0
    assert resp.summary.baseline_value == 120000.0
    assert resp.summary.absolute_change == -70000.0
    assert resp.summary.direction == "decrease"

    # Volume vs AOV decomposition present
    assert resp.decomposition is not None
    assert resp.decomposition.volume_effect < 0

    # Operational indicators captured
    assert resp.operational_indicators.observed_late_delivery_rate == 15.0
    assert resp.operational_indicators.late_delivery_rate_change == 7.0

    # Explanation contains non-causal language and key metrics
    assert "TOTAL_GMV decreased" in resp.explanation
    assert "office_furniture" in resp.explanation
    assert "These findings identify descriptive associations" in resp.explanation
