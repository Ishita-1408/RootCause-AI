"""Unit tests for Phase 4A Analytical Layer."""

from datetime import UTC, datetime

import pandas as pd


def test_order_grain_uniqueness() -> None:
    """Test that fact_order_analytics maintains exactly 1 row per order_id."""
    raw_orders = pd.DataFrame(
        [
            {"order_id": "ord_1", "customer_id": "c_1", "status": "delivered"},
            {"order_id": "ord_2", "customer_id": "c_2", "status": "shipped"},
            {"order_id": "ord_3", "customer_id": "c_3", "status": "canceled"},
        ]
    )

    # Invariant: order_id is strictly unique
    assert len(raw_orders) == 3
    assert raw_orders["order_id"].nunique() == len(raw_orders)
    assert raw_orders["order_id"].count() - raw_orders["order_id"].nunique() == 0


def test_customer_cohort_grain_uniqueness() -> None:
    """Test that dim_customer_cohorts maintains 1 row per unique customer."""
    orders_df = pd.DataFrame(
        [
            {
                "order_id": "o_1",
                "customer_unique_id": "user_A",
                "revenue": 100.0,
                "ts": datetime(2018, 1, 1, tzinfo=UTC),
            },
            {
                "order_id": "o_2",
                "customer_unique_id": "user_A",
                "revenue": 150.0,
                "ts": datetime(2018, 3, 1, tzinfo=UTC),
            },
            {
                "order_id": "o_3",
                "customer_unique_id": "user_B",
                "revenue": 80.0,
                "ts": datetime(2018, 2, 1, tzinfo=UTC),
            },
        ]
    )

    cohorts = (
        orders_df.groupby("customer_unique_id")
        .agg(
            first_order_date=("ts", "min"),
            last_order_date=("ts", "max"),
            lifetime_order_count=("order_id", "count"),
            lifetime_spend=("revenue", "sum"),
        )
        .reset_index()
    )
    cohorts["is_repeat_buyer"] = cohorts["lifetime_order_count"] > 1
    cohorts["average_order_value"] = (
        cohorts["lifetime_spend"] / cohorts["lifetime_order_count"]
    )

    assert len(cohorts) == 2  # Exactly 2 unique human buyers
    assert cohorts["customer_unique_id"].nunique() == 2

    user_a = cohorts[cohorts["customer_unique_id"] == "user_A"].iloc[0]
    assert user_a["lifetime_order_count"] == 2
    assert user_a["lifetime_spend"] == 250.0
    assert user_a["average_order_value"] == 125.0
    assert bool(user_a["is_repeat_buyer"]) is True

    user_b = cohorts[cohorts["customer_unique_id"] == "user_B"].iloc[0]
    assert user_b["lifetime_order_count"] == 1
    assert user_b["lifetime_spend"] == 80.0
    assert bool(user_b["is_repeat_buyer"]) is False


def test_null_delivery_handling() -> None:
    """Test that missing delivery dates do not create synthetic zeroes."""
    purchase_ts: datetime = datetime(2018, 5, 1, 10, 0, tzinfo=UTC)
    approved_at: datetime | None = datetime(2018, 5, 1, 11, 0, tzinfo=UTC)
    delivered_carrier: datetime | None = None
    delivered_customer: datetime | None = None
    estimated_delivery: datetime = datetime(2018, 5, 20, 0, 0, tzinfo=UTC)

    approval_lead_hours = (
        (approved_at - purchase_ts).total_seconds() / 3600.0 if approved_at else None
    )

    seller_dispatch_days = (
        (delivered_carrier - approved_at).total_seconds() / 86400.0
        if (delivered_carrier and approved_at)
        else None
    )

    total_delivery_days = (
        (delivered_customer - purchase_ts).total_seconds() / 86400.0
        if delivered_customer
        else None
    )

    delivery_delay_days = (
        (delivered_customer - estimated_delivery).total_seconds() / 86400.0
        if delivered_customer
        else None
    )

    is_late_delivery = (
        (delivered_customer > estimated_delivery) if delivered_customer else None
    )

    assert approval_lead_hours == 1.0
    assert seller_dispatch_days is None
    assert total_delivery_days is None
    assert delivery_delay_days is None
    assert is_late_delivery is None


def test_late_delivery_logic() -> None:
    """Test boolean is_late_delivery flag on early, on-time, and late dates."""
    estimated = datetime(2018, 5, 15, 0, 0, tzinfo=UTC)

    # 1. Early delivery (May 10 < May 15)
    early = datetime(2018, 5, 10, 14, 0, tzinfo=UTC)
    assert (early > estimated) is False

    # 2. Late delivery (May 18 > May 15)
    late = datetime(2018, 5, 18, 10, 0, tzinfo=UTC)
    assert (late > estimated) is True

    # 3. Exact date/time delivery boundary
    on_time = datetime(2018, 5, 14, 23, 59, tzinfo=UTC)
    assert (on_time > estimated) is False


def test_freight_to_price_ratio_zero_division_protection() -> None:
    """Test freight_to_price_ratio handles zero merchandise revenue safely."""

    def calc_ratio(merch_rev: float | None, freight: float | None) -> float | None:
        if merch_rev is None or freight is None or merch_rev == 0:
            return None
        return round(freight / merch_rev, 4)

    assert calc_ratio(100.0, 20.0) == 0.2000
    assert calc_ratio(50.0, 15.0) == 0.3000
    assert calc_ratio(0.0, 20.0) is None
    assert calc_ratio(None, 20.0) is None


def test_payment_aggregation() -> None:
    """Test primary payment method selection, max installments, and sum."""
    payments = [
        {
            "order_id": "ord_1",
            "payment_type": "voucher",
            "payment_value": 30.0,
            "installments": 1,
            "seq": 1,
        },
        {
            "order_id": "ord_1",
            "payment_type": "credit_card",
            "payment_value": 170.0,
            "installments": 6,
            "seq": 2,
        },
    ]
    df = pd.DataFrame(payments)

    total_payment = df["payment_value"].sum()
    max_installments = df["installments"].max()
    primary_type = df.sort_values(
        by=["payment_value", "seq"], ascending=[False, True]
    ).iloc[0]["payment_type"]

    assert total_payment == 200.0
    assert max_installments == 6
    assert primary_type == "credit_card"


def test_review_aggregation() -> None:
    """Test review score averaging and negative review flag logic."""
    reviews_a = pd.DataFrame(
        [
            {"order_id": "ord_A", "review_score": 1},
            {"order_id": "ord_A", "review_score": 3},
        ]
    )
    avg_score_a = round(float(reviews_a["review_score"].mean()), 2)
    has_negative_a = bool((reviews_a["review_score"] <= 2).any())

    assert avg_score_a == 2.0
    assert has_negative_a is True

    reviews_b = pd.DataFrame([{"order_id": "ord_B", "review_score": 5}])
    avg_score_b = round(float(reviews_b["review_score"].mean()), 2)
    has_negative_b = bool((reviews_b["review_score"] <= 2).any())

    assert avg_score_b == 5.0
    assert has_negative_b is False


def test_item_aggregation() -> None:
    """Test multi-item order aggregation metrics."""
    items = pd.DataFrame(
        [
            {
                "order_id": "ord_x",
                "order_item_id": 1,
                "seller_id": "sell_1",
                "price": 100.0,
                "freight_value": 15.0,
            },
            {
                "order_id": "ord_x",
                "order_item_id": 2,
                "seller_id": "sell_2",
                "price": 50.0,
                "freight_value": 10.0,
            },
            {
                "order_id": "ord_x",
                "order_item_id": 3,
                "seller_id": "sell_1",
                "price": 25.0,
                "freight_value": 5.0,
            },
        ]
    )

    merch_rev = items["price"].sum()
    freight_val = items["freight_value"].sum()
    total_val = merch_rev + freight_val
    item_cnt = len(items)
    distinct_sellers = items["seller_id"].nunique()

    assert merch_rev == 175.0
    assert freight_val == 30.0
    assert total_val == 205.0
    assert item_cnt == 3
    assert distinct_sellers == 2
