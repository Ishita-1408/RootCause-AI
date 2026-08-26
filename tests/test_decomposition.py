"""Unit tests for Phase 4B Descriptive Revenue Decomposition Engine."""

from datetime import date
from unittest.mock import MagicMock

from apps.analytics.decomposition import get_revenue_decomposition


def test_descriptive_decomposition_identity() -> None:
    """Test that Volume Effect + Price Effect strictly equals Total Revenue Change."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Baseline: Orders = 1,000, AOV = R$ 100 -> GMV = R$ 100,000
    # Current:  Orders = 1,200, AOV = R$ 125 -> GMV = R$ 150,000
    mock_cur.fetchone.side_effect = [
        {
            "gmv": 150000.0,
            "delivered_gmv": 140000.0,
            "average_order_value": 125.0,
            "revenue_per_customer": 130.0,
            "orders_count": 1200,
            "delivered_orders_count": 1150,
            "canceled_orders_count": 10,
            "items_sold_count": 1500,
            "unique_customers_count": 1100,
            "new_customers_count": 1000,
            "repeat_customers_count": 100,
            "repeat_buyer_rate_pct": 9.09,
            "late_delivery_rate_pct": 5.0,
            "avg_delivery_days": 10.0,
            "avg_seller_dispatch_days": 2.0,
            "avg_carrier_transit_days": 8.0,
            "avg_review_score": 4.5,
            "negative_review_rate_pct": 5.0,
            "freight_revenue": 20000.0,
            "freight_to_gmv_ratio": 0.1333,
        },
        {
            "gmv": 100000.0,
            "delivered_gmv": 90000.0,
            "average_order_value": 100.0,
            "revenue_per_customer": 110.0,
            "orders_count": 1000,
            "delivered_orders_count": 950,
            "canceled_orders_count": 10,
            "items_sold_count": 1200,
            "unique_customers_count": 900,
            "new_customers_count": 850,
            "repeat_customers_count": 50,
            "repeat_buyer_rate_pct": 5.56,
            "late_delivery_rate_pct": 6.0,
            "avg_delivery_days": 11.0,
            "avg_seller_dispatch_days": 2.5,
            "avg_carrier_transit_days": 8.5,
            "avg_review_score": 4.2,
            "negative_review_rate_pct": 8.0,
            "freight_revenue": 15000.0,
            "freight_to_gmv_ratio": 0.15,
        },
    ]

    decomp = get_revenue_decomposition(
        conn=mock_conn,
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 31),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 30),
    )

    assert decomp.decomposition_type == "descriptive_decomposition"
    assert decomp.total_revenue_change == 50000.0
    assert decomp.orders_change == 200
    assert decomp.aov_change == 25.0

    # Volume Effect = (1200 - 1000) * 100 = 20,000
    assert decomp.volume_effect == 20000.0
    # Price Effect = 1200 * (125 - 100) = 30,000
    assert decomp.price_effect == 30000.0

    # Exact Additive Identity Verification
    assert (
        round(decomp.volume_effect + decomp.price_effect, 2)
        == decomp.total_revenue_change
    )
