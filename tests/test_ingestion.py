import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from scripts.ingest_olist import (
    find_olist_zip,
    prepare_customers,
    prepare_order_items,
    prepare_orders,
    prepare_payments,
    prepare_product_categories,
    prepare_products,
    prepare_reviews,
    prepare_sellers,
    sanitize_val,
    to_optional_datetime,
    to_optional_float,
    to_optional_int,
)


def test_sanitize_helpers() -> None:
    """Test scalar sanitization and conversion helper functions."""
    assert sanitize_val(None) is None
    assert sanitize_val(float("nan")) is None
    assert sanitize_val("   ") is None
    assert sanitize_val("valid_text") == "valid_text"

    assert to_optional_int("42") == 42
    assert to_optional_int(42.0) == 42
    assert to_optional_int(None) is None
    assert to_optional_int("invalid") is None

    assert to_optional_float("123.45") == 123.45
    assert to_optional_float(None) is None
    assert to_optional_float("invalid") is None

    dt = to_optional_datetime("2018-05-09 10:15:30")
    assert isinstance(dt, datetime)
    assert dt.year == 2018
    assert to_optional_datetime(None) is None
    assert to_optional_datetime("invalid_date") is None


def test_prepare_product_categories() -> None:
    """Test category cleaning and unioning with catalog categories."""
    df_trans = pd.DataFrame(
        [
            {
                "product_category_name": "beleza_saude",
                "product_category_name_english": "health_beauty",
            },
            {
                "product_category_name": "informatica_acessorios",
                "product_category_name_english": "computers_accessories",
            },
        ]
    )
    df_prods = pd.DataFrame(
        [
            {"product_category_name": "beleza_saude"},
            {"product_category_name": "pc_gamer"},  # Extra untranslated category
            {"product_category_name": None},
        ]
    )

    records = prepare_product_categories(df_trans, df_prods)
    cat_dict = dict(records)

    assert "beleza_saude" in cat_dict
    assert cat_dict["beleza_saude"] == "health_beauty"
    assert "pc_gamer" in cat_dict
    assert cat_dict["pc_gamer"] is None
    assert len(records) == 3


def test_prepare_customers() -> None:
    """Test customer dataset record transformation."""
    df = pd.DataFrame(
        [
            {
                "customer_id": "c123",
                "customer_unique_id": "u456",
                "customer_zip_code_prefix": "01310",
                "customer_city": "sao paulo",
                "customer_state": "SP",
            }
        ]
    )
    records = prepare_customers(df)
    assert len(records) == 1
    assert records[0] == ("c123", "u456", "01310", "sao paulo", "SP")


def test_prepare_sellers() -> None:
    """Test seller dataset record transformation."""
    df = pd.DataFrame(
        [
            {
                "seller_id": "s999",
                "seller_zip_code_prefix": "14400",
                "seller_city": "franca",
                "seller_state": "SP",
            }
        ]
    )
    records = prepare_sellers(df)
    assert len(records) == 1
    assert records[0] == ("s999", "14400", "franca", "SP")


def test_prepare_products() -> None:
    """Test product dataset transformation and column name mapping."""
    df = pd.DataFrame(
        [
            {
                "product_id": "p001",
                "product_category_name": "perfumaria",
                "product_name_lenght": 40.0,
                "product_description_lenght": 250.0,
                "product_photos_qty": 2.0,
                "product_weight_g": 500.0,
                "product_length_cm": 15.0,
                "product_height_cm": 10.0,
                "product_width_cm": 12.0,
            }
        ]
    )
    records = prepare_products(df)
    assert len(records) == 1
    assert records[0] == ("p001", "perfumaria", 40, 250, 2, 500, 15, 10, 12)


def test_prepare_orders() -> None:
    """Test order header transformation and timestamp parsing."""
    df = pd.DataFrame(
        [
            {
                "order_id": "o001",
                "customer_id": "c123",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01 12:00:00",
                "order_approved_at": "2018-01-01 12:30:00",
                "order_delivered_carrier_date": "2018-01-02 08:00:00",
                "order_delivered_customer_date": "2018-01-05 16:00:00",
                "order_estimated_delivery_date": "2018-01-10 00:00:00",
            }
        ]
    )
    records = prepare_orders(df)
    assert len(records) == 1
    assert records[0][0] == "o001"
    assert records[0][2] == "delivered"
    assert isinstance(records[0][3], datetime)


def test_prepare_order_items() -> None:
    """Test order item line record transformation."""
    df = pd.DataFrame(
        [
            {
                "order_id": "o001",
                "order_item_id": 1,
                "product_id": "p001",
                "seller_id": "s999",
                "shipping_limit_date": "2018-01-05 12:00:00",
                "price": "99.90",
                "freight_value": "15.50",
            }
        ]
    )
    records = prepare_order_items(df)
    assert len(records) == 1
    assert records[0] == (
        "o001",
        1,
        "p001",
        "s999",
        datetime(2018, 1, 5, 12, 0, tzinfo=UTC),
        99.90,
        15.50,
    )


def test_prepare_payments() -> None:
    """Test payment record transformation."""
    df = pd.DataFrame(
        [
            {
                "order_id": "o001",
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 3,
                "payment_value": "115.40",
            }
        ]
    )
    records = prepare_payments(df)
    assert len(records) == 1
    assert records[0] == ("o001", 1, "credit_card", 3, 115.40)


def test_prepare_reviews_deduplication() -> None:
    """Test reviews transformation and composite PK deduplication."""
    df = pd.DataFrame(
        [
            {
                "review_id": "r001",
                "order_id": "o001",
                "review_score": 5,
                "review_comment_title": "Great",
                "review_comment_message": "Fast delivery",
                "review_creation_date": "2018-01-06 00:00:00",
                "review_answer_timestamp": "2018-01-07 10:00:00",
            },
            {
                # Duplicate composite PK
                "review_id": "r001",
                "order_id": "o001",
                "review_score": 5,
                "review_comment_title": "Great",
                "review_comment_message": "Fast delivery",
                "review_creation_date": "2018-01-06 00:00:00",
                "review_answer_timestamp": "2018-01-07 10:00:00",
            },
        ]
    )
    records = prepare_reviews(df)
    assert len(records) == 1
    assert records[0][0] == "r001"
    assert records[0][2] == 5


def test_find_olist_zip_in_temp_dir() -> None:
    """Test finding the ZIP archive in a directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_file = tmp_path / "olist.zip"
        with zipfile.ZipFile(zip_file, "w") as z:
            z.writestr("test.txt", "hello")

        found = find_olist_zip(tmp_path)
        assert found == zip_file
