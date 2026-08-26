"""Unit tests for Phase 4B Period Comparison Engine."""

from datetime import date
from unittest.mock import MagicMock

from apps.analytics.comparison import (
    compare_periods,
    compare_single_metric,
)


def test_compare_single_metric_growth() -> None:
    """Test comparison logic for positive growth."""
    comp = compare_single_metric("gmv", 150000.0, 100000.0)
    assert comp.metric == "gmv"
    assert comp.current_value == 150000.0
    assert comp.baseline_value == 100000.0
    assert comp.absolute_change == 50000.0
    assert comp.percentage_change == 50.0
    assert comp.direction == "increase"


def test_compare_single_metric_decline() -> None:
    """Test comparison logic for negative metric decline."""
    comp = compare_single_metric("orders_count", 800, 1000)
    assert comp.metric == "orders_count"
    assert comp.current_value == 800
    assert comp.baseline_value == 1000
    assert comp.absolute_change == -200
    assert comp.percentage_change == -20.0
    assert comp.direction == "decrease"


def test_compare_single_metric_unchanged_and_zero_baseline() -> None:
    """Test zero baseline and identical periods edge cases."""
    # Unchanged
    comp_same = compare_single_metric("gmv", 100.0, 100.0)
    assert comp_same.absolute_change == 0.0
    assert comp_same.percentage_change == 0.0
    assert comp_same.direction == "unchanged"

    # Zero baseline with positive current
    comp_zero_base = compare_single_metric("gmv", 50.0, 0.0)
    assert comp_zero_base.absolute_change == 50.0
    assert comp_zero_base.percentage_change == 100.0
    assert comp_zero_base.direction == "increase"

    # Both zero
    comp_both_zero = compare_single_metric("gmv", 0.0, 0.0)
    assert comp_both_zero.absolute_change == 0.0
    assert comp_both_zero.percentage_change == 0.0
    assert comp_both_zero.direction == "unchanged"


def test_compare_single_metric_null_handling() -> None:
    """Test undefined/None metric values."""
    comp_null_cur = compare_single_metric("late_delivery_rate_pct", None, 5.0)
    assert comp_null_cur.current_value is None
    assert comp_null_cur.baseline_value == 5.0
    assert comp_null_cur.percentage_change is None
    assert comp_null_cur.direction == "undefined"

    comp_null_both = compare_single_metric("late_delivery_rate_pct", None, None)
    assert comp_null_both.absolute_change is None
    assert comp_null_both.percentage_change is None
    assert comp_null_both.direction == "undefined"


def test_compare_periods_mocked() -> None:
    """Test full period comparison orchestration."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Mock return for current and baseline
    mock_cur.fetchone.side_effect = [
        {
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
        },
        {
            "gmv": 100000.0,
            "delivered_gmv": 95000.0,
            "average_order_value": 125.0,
            "revenue_per_customer": 130.0,
            "orders_count": 800,
            "delivered_orders_count": 760,
            "canceled_orders_count": 8,
            "items_sold_count": 960,
            "unique_customers_count": 769,
            "new_customers_count": 750,
            "repeat_customers_count": 19,
            "repeat_buyer_rate_pct": 2.47,
            "late_delivery_rate_pct": 5.0,
            "avg_delivery_days": 10.0,
            "avg_seller_dispatch_days": 2.5,
            "avg_carrier_transit_days": 7.5,
            "avg_review_score": 4.3,
            "negative_review_rate_pct": 9.5,
            "freight_revenue": 20000.0,
            "freight_to_gmv_ratio": 0.20,
        },
    ]

    res = compare_periods(
        conn=mock_conn,
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
    )

    assert "gmv" in res.comparisons
    assert res.comparisons["gmv"].absolute_change == 50000.0
    assert res.comparisons["gmv"].percentage_change == 50.0
    assert res.comparisons["orders_count"].absolute_change == 200
    assert res.comparisons["orders_count"].direction == "increase"
