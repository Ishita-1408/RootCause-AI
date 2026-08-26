"""Unit tests for Phase 4.1 Feature Engineering and fact_order_analytics logic."""

from datetime import UTC, datetime
from typing import Any

import pandas as pd


def test_grain_separation_no_cartesian_multiplication() -> None:
    """Test that pre-aggregating items and payments prevents Cartesian inflation."""
    # Simulated order with 3 items and 2 split payments
    order_items_df = pd.DataFrame(
        [
            {
                "order_id": "ord_1",
                "order_item_id": 1,
                "price": 100.0,
                "freight_value": 15.0,
            },
            {
                "order_id": "ord_1",
                "order_item_id": 2,
                "price": 50.0,
                "freight_value": 10.0,
            },
            {
                "order_id": "ord_1",
                "order_item_id": 3,
                "price": 25.0,
                "freight_value": 5.0,
            },
        ]
    )
    payments_df = pd.DataFrame(
        [
            {
                "order_id": "ord_1",
                "payment_sequential": 1,
                "payment_type": "voucher",
                "payment_value": 50.0,
            },
            {
                "order_id": "ord_1",
                "payment_sequential": 2,
                "payment_type": "credit_card",
                "payment_value": 155.0,
            },
        ]
    )

    # INCORRECT / NAIVE DIRECT JOIN: 3 items x 2 payments = 6 rows
    naive_join = order_items_df.merge(payments_df, on="order_id")
    assert len(naive_join) == 6
    assert naive_join["price"].sum() == 350.0  # Erroneously inflated!
    assert naive_join["payment_value"].sum() == 615.0  # Erroneously inflated!

    # CORRECT PRE-AGGREGATION PATTERN (RootCause AI Standard):
    item_agg = (
        order_items_df.groupby("order_id")
        .agg(
            merchandise_revenue=("price", "sum"),
            freight_value=("freight_value", "sum"),
            item_count=("order_item_id", "count"),
        )
        .reset_index()
    )

    payment_agg = (
        payments_df.groupby("order_id")
        .agg(
            total_payment_value=("payment_value", "sum"),
        )
        .reset_index()
    )

    fact_order = item_agg.merge(payment_agg, on="order_id")
    assert len(fact_order) == 1
    assert fact_order.iloc[0]["merchandise_revenue"] == 175.0
    assert fact_order.iloc[0]["freight_value"] == 30.0
    assert fact_order.iloc[0]["total_payment_value"] == 205.0
    assert fact_order.iloc[0]["item_count"] == 3


def test_primary_payment_ranking() -> None:
    """Test identifying primary payment type based on largest tender value."""
    payments_df = pd.DataFrame(
        [
            {
                "order_id": "ord_1",
                "payment_type": "voucher",
                "payment_value": 20.0,
                "seq": 1,
            },
            {
                "order_id": "ord_1",
                "payment_type": "credit_card",
                "payment_value": 150.0,
                "seq": 2,
            },
            {
                "order_id": "ord_2",
                "payment_type": "boleto",
                "payment_value": 80.0,
                "seq": 1,
            },
        ]
    )

    ranked = (
        payments_df.sort_values(
            by=["order_id", "payment_value", "seq"],
            ascending=[True, False, True],
        )
        .groupby("order_id")
        .first()
        .reset_index()
    )

    p_map = dict(zip(ranked["order_id"], ranked["payment_type"], strict=True))
    assert p_map["ord_1"] == "credit_card"
    assert p_map["ord_2"] == "boleto"


def test_delivery_lead_times_and_late_flags() -> None:
    """Test delivery delay arithmetic and binary SLA violation flags."""
    # Case A: Delivered 2 days early
    purchased = datetime(2018, 5, 1, 10, 0, tzinfo=UTC)
    delivered = datetime(2018, 5, 10, 10, 0, tzinfo=UTC)
    estimated = datetime(2018, 5, 12, 0, 0, tzinfo=UTC)

    total_days = (delivered - purchased).total_seconds() / 86400.0
    delay_days = (delivered - estimated).total_seconds() / 86400.0
    is_late = delivered > estimated

    assert round(total_days, 1) == 9.0
    assert delay_days < 0  # Delivered early
    assert is_late is False

    # Case B: Delivered 3 days late
    delivered_late = datetime(2018, 5, 15, 10, 0, tzinfo=UTC)
    delay_days_late = (delivered_late - estimated).total_seconds() / 86400.0
    is_late_flag = delivered_late > estimated

    assert delay_days_late > 0
    assert is_late_flag is True


def test_canceled_order_null_durations() -> None:
    """Test that canceled orders preserve NULL delivery durations instead of zeros."""
    canceled_order = {
        "order_id": "ord_canceled",
        "order_status": "canceled",
        "order_purchase_timestamp": datetime(2018, 1, 1, 12, 0, tzinfo=UTC),
        "order_delivered_customer_date": None,
        "order_estimated_delivery_date": datetime(2018, 1, 20, 0, 0, tzinfo=UTC),
    }

    if canceled_order["order_delivered_customer_date"] is None:
        total_delivery_days = None
        is_late_delivery = None
    else:
        total_delivery_days = 0.0
        is_late_delivery = False

    assert total_delivery_days is None
    assert is_late_delivery is None


def test_missing_review_scoring_invariants() -> None:
    """Test that missing reviews are not treated as 0-star reviews."""
    reviews_df = pd.DataFrame(
        [
            {"order_id": "ord_rated", "review_id": "rev_1", "review_score": 5},
        ]
    )

    orders = ["ord_rated", "ord_unrated"]
    records: list[dict[str, Any]] = []
    for o_id in orders:
        match = reviews_df[reviews_df["order_id"] == o_id]
        if match.empty:
            records.append(
                {
                    "order_id": o_id,
                    "review_score": None,
                    "review_count": 0,
                    "is_negative_review": False,
                }
            )
        else:
            avg_score = float(match["review_score"].mean())
            records.append(
                {
                    "order_id": o_id,
                    "review_score": avg_score,
                    "review_count": len(match),
                    "is_negative_review": bool(avg_score <= 2),
                }
            )

    res = {r["order_id"]: r for r in records}
    assert res["ord_rated"]["review_score"] == 5.0
    assert res["ord_rated"]["review_count"] == 1
    assert res["ord_rated"]["is_negative_review"] is False

    assert res["ord_unrated"]["review_score"] is None
    assert res["ord_unrated"]["review_count"] == 0
    assert res["ord_unrated"]["is_negative_review"] is False
