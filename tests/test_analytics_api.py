"""Integration tests for Phase 4B Analytics FastAPI endpoints."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.analytics.models import (
    DimensionBreakdownResponse,
    KPISummary,
    PeriodComparisonResponse,
    RevenueDecomposition,
)
from apps.api.main import app

client = TestClient(app)


@patch("apps.api.routers.analytics.get_db_connection")
@patch("apps.api.routers.analytics.get_kpis")
def test_get_kpis_endpoint_success(
    mock_get_kpis: MagicMock, mock_conn: MagicMock
) -> None:
    """Test GET /api/v1/analytics/kpis endpoint."""
    mock_get_kpis.return_value = KPISummary(
        start_date=date(2018, 5, 1),
        end_date=date(2018, 5, 31),
        gmv=150000.0,
        delivered_gmv=140000.0,
        average_order_value=150.0,
        revenue_per_customer=160.0,
        orders_count=1000,
        delivered_orders_count=950,
        canceled_orders_count=10,
        items_sold_count=1200,
        unique_customers_count=937,
        new_customers_count=900,
        repeat_customers_count=37,
        repeat_buyer_rate_pct=3.95,
        late_delivery_rate_pct=7.5,
        avg_delivery_days=11.2,
        avg_seller_dispatch_days=2.8,
        avg_carrier_transit_days=8.4,
        avg_review_score=4.15,
        negative_review_rate_pct=12.3,
        freight_revenue=25000.0,
        freight_to_gmv_ratio=0.1667,
    )

    response = client.get(
        "/api/v1/analytics/kpis",
        params={"start_date": "2018-05-01", "end_date": "2018-05-31"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gmv"] == 150000.0
    assert data["orders_count"] == 1000


@patch("apps.api.routers.analytics.get_db_connection")
@patch("apps.api.routers.analytics.compare_periods")
def test_compare_kpis_endpoint_success(
    mock_compare: MagicMock, mock_conn: MagicMock
) -> None:
    """Test GET /api/v1/analytics/compare endpoint."""
    mock_compare.return_value = PeriodComparisonResponse(
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
        comparisons={},
    )

    response = client.get(
        "/api/v1/analytics/compare",
        params={
            "current_start": "2018-05-01",
            "current_end": "2018-05-31",
            "baseline_start": "2018-04-01",
            "baseline_end": "2018-04-30",
        },
    )
    assert response.status_code == 200


@patch("apps.api.routers.analytics.get_db_connection")
@patch("apps.api.routers.analytics.get_dimensional_breakdown")
def test_breakdown_endpoint_success(mock_bd: MagicMock, mock_conn: MagicMock) -> None:
    """Test GET /api/v1/analytics/breakdown endpoint."""
    mock_bd.return_value = DimensionBreakdownResponse(
        metric="gmv",
        dimension="customer_state",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
        total_current_value=150000.0,
        total_baseline_value=100000.0,
        total_change=50000.0,
        slices=[],
    )

    response = client.get(
        "/api/v1/analytics/breakdown",
        params={
            "metric": "gmv",
            "dimension": "customer_state",
            "current_start": "2018-05-01",
            "current_end": "2018-05-31",
            "baseline_start": "2018-04-01",
            "baseline_end": "2018-04-30",
        },
    )
    assert response.status_code == 200


@patch("apps.api.routers.analytics.get_db_connection")
@patch("apps.api.routers.analytics.get_revenue_decomposition")
def test_decomposition_endpoint_success(
    mock_dec: MagicMock, mock_conn: MagicMock
) -> None:
    """Test GET /api/v1/analytics/decomposition endpoint."""
    mock_dec.return_value = RevenueDecomposition(
        decomposition_type="descriptive_decomposition",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
        current_revenue=150000.0,
        baseline_revenue=100000.0,
        total_revenue_change=50000.0,
        current_orders=1200,
        baseline_orders=1000,
        orders_change=200,
        orders_change_pct=20.0,
        current_aov=125.0,
        baseline_aov=100.0,
        aov_change=25.0,
        aov_change_pct=25.0,
        volume_effect=20000.0,
        price_effect=30000.0,
    )

    response = client.get(
        "/api/v1/analytics/decomposition",
        params={
            "current_start": "2018-05-01",
            "current_end": "2018-05-31",
            "baseline_start": "2018-04-01",
            "baseline_end": "2018-04-30",
        },
    )
    assert response.status_code == 200
    assert response.json()["volume_effect"] == 20000.0


def test_invalid_date_range_validation() -> None:
    """Test that end_date earlier than start_date returns 422 error."""
    response = client.get(
        "/api/v1/analytics/kpis",
        params={"start_date": "2018-05-31", "end_date": "2018-05-01"},
    )
    assert response.status_code == 422
