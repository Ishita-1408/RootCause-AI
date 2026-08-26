from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.analytics.diagnostics.engine import run_root_cause_analysis
from apps.analytics.diagnostics.models import (
    DiagnosticRequest,
    DiagnosticResponse,
    DiagnosticSummary,
    RevenueDecomposition,
)
from apps.analytics.diagnostics.scorers import compute_root_cause_score
from apps.api.main import app

client = TestClient(app)


# 1. Test Revenue Decomposition Mathematical Identity
def test_revenue_decomposition_identity() -> None:
    """Test exact mathematical additive decomposition identity."""
    delta_v = -500.0
    delta_a = 10.0
    base_orders = 2000.0
    base_aov = 100.0

    cur_orders = base_orders + delta_v  # 1500
    cur_aov = base_aov + delta_a  # 110
    cur_gmv = cur_orders * cur_aov  # 165,000
    base_gmv = base_orders * base_aov  # 200,000
    actual_gmv_change = cur_gmv - base_gmv  # -35,000

    vol_effect = delta_v * base_aov  # -50,000
    aov_effect = base_orders * delta_a  # +20,000
    interaction_effect = delta_v * delta_a  # -5,000

    assert vol_effect + aov_effect + interaction_effect == actual_gmv_change

    decomp = RevenueDecomposition(
        volume_effect=vol_effect,
        aov_effect=aov_effect,
        interaction_effect=interaction_effect,
        total_revenue_change=actual_gmv_change,
        volume_contribution_pct=round((vol_effect / actual_gmv_change) * 100.0, 2),
        aov_contribution_pct=round((aov_effect / actual_gmv_change) * 100.0, 2),
        interaction_contribution_pct=round(
            (interaction_effect / actual_gmv_change) * 100.0, 2
        ),
    )

    assert decomp.volume_contribution_pct == 142.86
    assert decomp.aov_contribution_pct == -57.14
    assert decomp.interaction_contribution_pct == 14.29


# 2. Test Multi-Factor Root-Cause Scoring Boundedness
def test_compute_root_cause_score_bounds() -> None:
    """Test scoring algorithm returns valid numbers in [0.0, 1.0]."""
    assert compute_root_cause_score(magnitude=0.0, contribution=0.0) == 0.20
    assert (
        compute_root_cause_score(magnitude=1.0, contribution=1.0, consistency=1.0)
        == 1.0
    )
    assert (
        compute_root_cause_score(magnitude=0.5, contribution=0.8, consistency=0.5)
        == 0.64
    )


# 3. Test Request Validation
def test_diagnostic_request_validation() -> None:
    """Test invalid windows reject gracefully."""
    with pytest.raises(ValueError, match="baseline_window must be at least"):
        DiagnosticRequest(
            metric="total_gmv",
            anomaly_date=date(2018, 1, 15),
            comparison_window=28,
            baseline_window=7,  # Invalid: baseline shorter than comparison
        )


# 4. Test Mocked Diagnostic Engine Execution
@patch("apps.analytics.diagnostics.engine.fetch_dimension_slices_for_diagnostic")
@patch("apps.analytics.diagnostics.engine.fetch_period_diagnostics")
def test_run_root_cause_analysis_mocked(
    mock_fetch_period: MagicMock,
    mock_fetch_slices: MagicMock,
) -> None:
    """Test full diagnostic orchestration with mocked DB calls."""
    mock_conn = MagicMock()

    # Mock cur vs base period returns
    mock_fetch_period.side_effect = [
        # Current period (7 days)
        {
            "orders_count": 800.0,
            "total_gmv": 80000.0,
            "average_order_value": 100.0,
            "late_delivery_rate_pct": 14.5,
            "avg_review_score": 3.8,
            "seller_dispatch_days": 3.2,
            "carrier_transit_days": 13.5,
            "cancellation_rate_pct": 0.5,
            "negative_review_rate_pct": 18.0,
            "one_star_review_rate_pct": 12.0,
            "two_star_review_rate_pct": 6.0,
        },
        # Baseline period (28 days, raw)
        {
            "orders_count": 4000.0,  # normalized -> 1000.0
            "total_gmv": 480000.0,  # normalized -> 120000.0
            "average_order_value": 120.0,
            "late_delivery_rate_pct": 8.0,
            "avg_review_score": 4.2,
            "seller_dispatch_days": 2.5,
            "carrier_transit_days": 10.0,
            "cancellation_rate_pct": 0.2,
            "negative_review_rate_pct": 12.0,
            "one_star_review_rate_pct": 8.0,
            "two_star_review_rate_pct": 4.0,
        },
    ]

    # Mock dimensional slice returns
    mock_fetch_slices.return_value = [
        {
            "slice_value": "telefonia",
            "actual_value": 20000.0,
            "baseline_value": 40000.0,
        },
        {"slice_value": "bebes", "actual_value": 15000.0, "baseline_value": 20000.0},
    ]

    req = DiagnosticRequest(
        metric="total_gmv",
        anomaly_date=date(2018, 1, 15),
        comparison_window=7,
        baseline_window=28,
    )

    res = run_root_cause_analysis(conn=mock_conn, request=req)

    assert isinstance(res, DiagnosticResponse)
    assert res.summary.primary_driver == "ORDER_VOLUME"
    assert res.summary.actual_value == 80000.0
    assert res.summary.baseline_value == 120000.0
    assert res.summary.absolute_change == -40000.0
    assert res.summary.percentage_change == -33.33

    # Operational signals identified late delivery deterioration
    late_op = next(
        o for o in res.operational_signals if o.metric == "late_delivery_rate_pct"
    )
    assert late_op.actual_value == 14.5
    assert late_op.severity == "critical"

    # Root cause ranking contains volume and category findings
    assert len(res.root_cause_ranking) >= 2
    assert res.root_cause_ranking[0].rank == 1


# 5. Test Diagnostic API Endpoints
def test_diagnostic_health_endpoint() -> None:
    """Test GET /api/v1/diagnostics/health endpoint."""
    resp = client.get("/api/v1/diagnostics/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "healthy",
        "service": "diagnostics_engine",
    }


@patch("apps.api.routers.diagnostics.get_db_connection")
@patch("apps.api.routers.diagnostics.run_root_cause_analysis")
def test_diagnostic_root_cause_endpoint_success(
    mock_run: MagicMock, mock_conn: MagicMock
) -> None:
    """Test POST /api/v1/diagnostics/root-cause endpoint."""
    req = DiagnosticRequest(
        metric="total_gmv",
        anomaly_date=date(2018, 1, 15),
        comparison_window=7,
        baseline_window=28,
    )

    mock_run.return_value = DiagnosticResponse(
        request=req,
        summary=DiagnosticSummary(
            metric="total_gmv",
            anomaly_date=date(2018, 1, 15),
            comparison_period_start=date(2018, 1, 9),
            comparison_period_end=date(2018, 1, 15),
            baseline_period_start=date(2017, 12, 11),
            baseline_period_end=date(2018, 1, 8),
            actual_value=80000.0,
            baseline_value=100000.0,
            absolute_change=-20000.0,
            percentage_change=-20.0,
            primary_driver="ORDER_VOLUME",
            confidence_score=0.85,
        ),
        revenue_decomposition=RevenueDecomposition(
            volume_effect=-15000.0,
            aov_effect=-5000.0,
            interaction_effect=0.0,
            total_revenue_change=-20000.0,
            volume_contribution_pct=75.0,
            aov_contribution_pct=25.0,
            interaction_contribution_pct=0.0,
        ),
        top_dimensional_contributors=[],
        operational_signals=[],
        satisfaction_signals=[],
        root_cause_ranking=[],
        conclusion="Primary driver was lower order volume.",
    )

    response = client.post(
        "/api/v1/diagnostics/root-cause",
        json={
            "metric": "total_gmv",
            "anomaly_date": "2018-01-15",
            "comparison_window": 7,
            "baseline_window": 28,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["primary_driver"] == "ORDER_VOLUME"
    assert data["summary"]["absolute_change"] == -20000.0
