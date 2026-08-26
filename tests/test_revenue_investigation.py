"""Unit and integration tests for the Revenue Investigation Engine."""

from datetime import date
from unittest.mock import MagicMock, patch

import psycopg
import pytest
from fastapi.testclient import TestClient

from apps.analytics.models import (
    PeriodSummary,
    RevenueInvestigationRequest,
)
from apps.analytics.revenue_analysis import (
    analyze_dimension_breakdown,
    build_finding_explanation,
    compute_change_metrics,
)
from apps.api.main import app

client = TestClient(app)


def test_compute_change_metrics_revenue_increase() -> None:
    """Test delta calculation and volume/AOV decomposition for growth."""
    baseline = PeriodSummary(
        start_date=date(2018, 4, 1),
        end_date=date(2018, 4, 30),
        total_revenue=100000.0,
        order_count=1000,
        average_order_value=100.0,
    )
    current = PeriodSummary(
        start_date=date(2018, 5, 1),
        end_date=date(2018, 5, 31),
        total_revenue=150000.0,
        order_count=1200,
        average_order_value=125.0,
    )

    change = compute_change_metrics(current, baseline)

    assert change.revenue_change == 50000.0
    assert change.revenue_change_pct == 50.0
    assert change.order_count_change == 200
    assert change.order_count_change_pct == 20.0
    assert change.aov_change == 25.0
    assert change.aov_change_pct == 25.0

    # Verify exact mathematical additive identity
    assert change.volume_effect == 200 * 100.0  # +20,000
    assert change.aov_effect == 1200 * 25.0  # +30,000
    assert round(change.volume_effect + change.aov_effect, 2) == change.revenue_change


def test_compute_change_metrics_revenue_decrease() -> None:
    """Test delta calculation and volume/AOV decomposition for decline."""
    baseline = PeriodSummary(
        start_date=date(2018, 5, 1),
        end_date=date(2018, 5, 31),
        total_revenue=150000.0,
        order_count=1200,
        average_order_value=125.0,
    )
    current = PeriodSummary(
        start_date=date(2018, 6, 1),
        end_date=date(2018, 6, 30),
        total_revenue=90000.0,
        order_count=900,
        average_order_value=100.0,
    )

    change = compute_change_metrics(current, baseline)

    assert change.revenue_change == -60000.0
    assert change.revenue_change_pct == -40.0
    assert change.order_count_change == -300
    assert change.aov_change == -25.0

    # Volume Effect = (-300) * 125 = -37,500
    assert change.volume_effect == -37500.0
    # AOV Effect = 900 * (-25) = -22,500
    assert change.aov_effect == -22500.0
    assert round(change.volume_effect + change.aov_effect, 2) == change.revenue_change


def test_compute_change_metrics_zero_baseline() -> None:
    """Test edge cases with zero baseline or identical periods."""
    zero_baseline = PeriodSummary(
        start_date=date(2017, 1, 1),
        end_date=date(2017, 1, 31),
        total_revenue=0.0,
        order_count=0,
        average_order_value=0.0,
    )
    current = PeriodSummary(
        start_date=date(2017, 2, 1),
        end_date=date(2017, 2, 28),
        total_revenue=50000.0,
        order_count=500,
        average_order_value=100.0,
    )

    change = compute_change_metrics(current, zero_baseline)
    assert change.revenue_change == 50000.0
    assert change.revenue_change_pct == 100.0
    assert change.volume_effect == 0.0
    assert change.aov_effect == 50000.0

    # Identical periods
    same_change = compute_change_metrics(current, current)
    assert same_change.revenue_change == 0.0
    assert same_change.revenue_change_pct == 0.0


def test_request_validation_invalid_ranges() -> None:
    """Test that chronologically inverted date ranges fail validation."""
    with pytest.raises(ValueError, match="end_date cannot be earlier"):
        RevenueInvestigationRequest(
            start_date=date(2018, 5, 31),
            end_date=date(2018, 5, 1),
            baseline_start_date=date(2018, 4, 1),
            baseline_end_date=date(2018, 4, 30),
        )

    with pytest.raises(ValueError, match="baseline_end_date cannot be earlier"):
        RevenueInvestigationRequest(
            start_date=date(2018, 5, 1),
            end_date=date(2018, 5, 31),
            baseline_start_date=date(2018, 4, 30),
            baseline_end_date=date(2018, 4, 1),
        )


def test_finding_explanation_generation() -> None:
    """Test deterministic narrative explanation formatting."""
    expl_decline = build_finding_explanation(
        dimension_value="SP",
        dimension_name="customer_state",
        current_val=100000.0,
        baseline_val=140000.0,
        abs_change=-40000.0,
        contrib_pct=40.0,
        total_change=-100000.0,
    )
    assert (
        "SP contributed approximately 40.0% to the total revenue decline"
        in expl_decline
    )

    expl_offset = build_finding_explanation(
        dimension_value="RJ",
        dimension_name="customer_state",
        current_val=30000.0,
        baseline_val=20000.0,
        abs_change=10000.0,
        contrib_pct=-10.0,
        total_change=-100000.0,
    )
    assert "partially counteracting" in expl_offset


def test_analyze_dimension_breakdown_mocked() -> None:
    """Test dimensional ranking and contribution calculation using mocked DB."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchall.return_value = [
        {
            "slice_value": "SP",
            "current_value": 80000.0,
            "baseline_value": 140000.0,
        },
        {
            "slice_value": "RJ",
            "current_value": 40000.0,
            "baseline_value": 70000.0,
        },
        {
            "slice_value": "MG",
            "current_value": 20000.0,
            "baseline_value": 30000.0,
        },
    ]

    findings = analyze_dimension_breakdown(
        conn=mock_conn,
        dimension="customer_state",
        start_date=date(2018, 5, 1),
        end_date=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
        total_revenue_change=-100000.0,
    )

    assert len(findings) == 3
    assert findings[0].dimension_value == "SP"
    assert findings[0].rank == 1
    assert findings[0].contribution_percentage == 60.0

    assert findings[1].dimension_value == "RJ"
    assert findings[1].rank == 2
    assert findings[1].contribution_percentage == 30.0


def test_api_revenue_investigation_endpoint_success() -> None:
    """Test POST /api/v1/investigations/revenue with mocked database."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchone.side_effect = [
        {
            "total_revenue": 150000.0,
            "order_count": 1000,
            "average_order_value": 150.0,
        },
        {
            "total_revenue": 100000.0,
            "order_count": 800,
            "average_order_value": 125.0,
        },
    ]
    mock_cur.fetchall.return_value = [
        {
            "slice_value": "SP",
            "current_value": 60000.0,
            "baseline_value": 40000.0,
        },
    ]

    with patch("apps.api.routers.investigations.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        payload = {
            "start_date": "2018-05-01",
            "end_date": "2018-05-31",
            "baseline_start_date": "2018-04-01",
            "baseline_end_date": "2018-04-30",
        }

        response = client.post("/api/v1/investigations/revenue", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["metric"] == "revenue"
    assert "investigation_id" in data
    assert data["current_period"]["total_revenue"] == 150000.0
    assert data["baseline_period"]["total_revenue"] == 100000.0
    assert data["change"]["revenue_change"] == 50000.0
    assert data["change"]["volume_effect"] == 25000.0
    assert data["change"]["aov_effect"] == 25000.0
    assert len(data["findings"]) > 0


def test_api_revenue_investigation_validation_error() -> None:
    """Test 422 response when invalid date intervals are posted."""
    payload = {
        "start_date": "2018-05-31",
        "end_date": "2018-05-01",
        "baseline_start_date": "2018-04-01",
        "baseline_end_date": "2018-04-30",
    }
    response = client.post("/api/v1/investigations/revenue", json=payload)
    assert response.status_code == 422


def test_api_revenue_investigation_db_error() -> None:
    """Test 503 response when database fails."""
    with patch(
        "apps.api.routers.investigations.get_db_connection",
        side_effect=psycopg.OperationalError("Connection lost"),
    ):
        payload = {
            "start_date": "2018-05-01",
            "end_date": "2018-05-31",
            "baseline_start_date": "2018-04-01",
            "baseline_end_date": "2018-04-30",
        }
        response = client.post("/api/v1/investigations/revenue", json=payload)

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Database service unavailable during investigation."
    )
