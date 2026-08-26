"""Unit tests for Phase 4B KPI Query Service and metric calculation logic."""

from datetime import date
from unittest.mock import MagicMock

from apps.analytics.metrics import (
    get_customer_kpi,
    get_delivery_kpi,
    get_kpis,
    get_order_volume_kpi,
    get_revenue_kpi,
    get_review_kpi,
)


def test_get_kpis_populated_mocked() -> None:
    """Test get_kpis parsing all 20 business metrics correctly from SQL cursor."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchone.return_value = {
        "gmv": 150000.0,
        "delivered_gmv": 140000.0,
        "average_order_value": 150.0,
        "revenue_per_customer": 160.0,
        "orders_count": 1000,
        "delivered_orders_count": 950,
        "canceled_orders_count": 10,
        "items_sold_count": 1200,
        "unique_customers_count": 937,
        "new_customers_count": 900,
        "repeat_customers_count": 37,
        "repeat_buyer_rate_pct": 3.95,
        "late_delivery_rate_pct": 7.5,
        "avg_delivery_days": 11.2,
        "avg_seller_dispatch_days": 2.8,
        "avg_carrier_transit_days": 8.4,
        "avg_review_score": 4.15,
        "negative_review_rate_pct": 12.3,
        "freight_revenue": 25000.0,
        "freight_to_gmv_ratio": 0.1667,
    }

    kpi = get_kpis(mock_conn, date(2018, 5, 1), date(2018, 5, 31))

    assert kpi.gmv == 150000.0
    assert kpi.delivered_gmv == 140000.0
    assert kpi.average_order_value == 150.0
    assert kpi.orders_count == 1000
    assert kpi.delivered_orders_count == 950
    assert kpi.canceled_orders_count == 10
    assert kpi.unique_customers_count == 937
    assert kpi.repeat_buyer_rate_pct == 3.95
    assert kpi.late_delivery_rate_pct == 7.5
    assert kpi.avg_review_score == 4.15
    assert kpi.freight_to_gmv_ratio == 0.1667


def test_get_kpis_empty_mocked() -> None:
    """Test get_kpis safely returns None for undefined ratios when 0 orders exist."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = None

    kpi = get_kpis(mock_conn, date(2017, 1, 1), date(2017, 1, 31))

    assert kpi.gmv == 0.0
    assert kpi.orders_count == 0
    assert kpi.average_order_value is None
    assert kpi.late_delivery_rate_pct is None
    assert kpi.avg_review_score is None
    assert kpi.freight_to_gmv_ratio is None


def test_kpi_category_helpers() -> None:
    """Test specialized metric getter helpers."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    mock_cur.fetchone.return_value = {
        "gmv": 100000.0,
        "delivered_gmv": 90000.0,
        "average_order_value": 100.0,
        "revenue_per_customer": 100.0,
        "orders_count": 1000,
        "delivered_orders_count": 900,
        "canceled_orders_count": 10,
        "items_sold_count": 1100,
        "unique_customers_count": 950,
        "new_customers_count": 900,
        "repeat_customers_count": 50,
        "repeat_buyer_rate_pct": 5.26,
        "late_delivery_rate_pct": 6.5,
        "avg_delivery_days": 10.5,
        "avg_seller_dispatch_days": 2.5,
        "avg_carrier_transit_days": 8.0,
        "avg_review_score": 4.2,
        "negative_review_rate_pct": 10.0,
        "freight_revenue": 18000.0,
        "freight_to_gmv_ratio": 0.18,
    }

    start = date(2018, 5, 1)
    end = date(2018, 5, 31)

    rev = get_revenue_kpi(mock_conn, start, end)
    vol = get_order_volume_kpi(mock_conn, start, end)
    cust = get_customer_kpi(mock_conn, start, end)
    ops = get_delivery_kpi(mock_conn, start, end)
    sent = get_review_kpi(mock_conn, start, end)

    assert rev["gmv"] == 100000.0
    assert vol["orders_count"] == 1000
    assert cust["repeat_customers_count"] == 50
    assert ops["late_delivery_rate_pct"] == 6.5
    assert sent["avg_review_score"] == 4.2
