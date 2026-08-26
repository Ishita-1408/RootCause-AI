"""Olist Brazilian E-Commerce Data Ingestion Pipeline.

Extracts CSV datasets directly from data/raw/olist.zip, validates and cleans
the data, and loads it into Supabase PostgreSQL using plain psycopg SQL
in foreign-key safe order.
"""

import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg

# Ensure project root is in sys.path when script is executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.config import get_settings  # noqa: E402

# Mapping of Olist CSV file names to destination database tables
CSV_TABLE_MAP: dict[str, str] = {
    "product_category_name_translation.csv": "product_categories",
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "olist_products_dataset.csv": "products",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
}

# Ingestion load order respecting foreign-key dependencies
LOAD_ORDER: list[str] = [
    "product_categories",
    "customers",
    "sellers",
    "products",
    "orders",
    "order_items",
    "payments",
    "reviews",
]


def find_olist_zip(raw_dir: Path | None = None) -> Path:
    """Locate the Olist ZIP archive in the raw data directory."""
    if raw_dir is None:
        raw_dir = Path("data/raw")

    if not raw_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {raw_dir}")

    # Look for olist.zip or any zip archive in data/raw
    standard_zip = raw_dir / "olist.zip"
    if standard_zip.exists():
        return standard_zip

    zip_files = list(raw_dir.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No ZIP archives found in {raw_dir}")

    return zip_files[0]


def read_csv_from_zip(zip_ref: zipfile.ZipFile, csv_filename: str) -> pd.DataFrame:
    """Read a CSV file directly from an open ZIP archive into a pandas DataFrame."""
    namelist = zip_ref.namelist()
    match = next(
        (name for name in namelist if name.lower().endswith(csv_filename.lower())),
        None,
    )
    if not match:
        raise FileNotFoundError(f"'{csv_filename}' not found in ZIP archive")

    with zip_ref.open(match) as file_handle:
        return pd.read_csv(file_handle, encoding="utf-8")


def sanitize_val(val: Any) -> Any:
    """Convert pandas/numpy NaN, NaT, and null-like objects to Python None."""
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if isinstance(val, (np.floating, np.integer)):
        return val.item()
    if pd.isna(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def to_optional_int(val: Any) -> int | None:
    """Convert a value to integer or None."""
    clean = sanitize_val(val)
    if clean is None:
        return None
    try:
        return int(float(clean))
    except (ValueError, TypeError):
        return None


def to_optional_float(val: Any) -> float | None:
    """Convert a value to float or None."""
    clean = sanitize_val(val)
    if clean is None:
        return None
    try:
        return float(clean)
    except (ValueError, TypeError):
        return None


def to_optional_datetime(val: Any) -> datetime | None:
    """Convert a date/time string or timestamp to Python datetime or None."""
    clean = sanitize_val(val)
    if clean is None:
        return None
    try:
        ts = pd.to_datetime(clean, utc=True)
        if pd.isna(ts):
            return None
        dt_val: datetime = ts.to_pydatetime()
        return dt_val
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Data Transformation & Cleaning Functions (Unit-Testable)
# -----------------------------------------------------------------------------


def prepare_product_categories(
    df_trans: pd.DataFrame, df_products: pd.DataFrame
) -> list[tuple[str, str | None]]:
    """Clean and union product categories from translations and products catalog.

    Ensures all distinct category names in products exist in product_categories
    so foreign keys are never violated.
    """
    category_map: dict[str, str | None] = {}

    for _, row in df_trans.iterrows():
        cat_pt = sanitize_val(row.get("product_category_name"))
        cat_en = sanitize_val(row.get("product_category_name_english"))
        if cat_pt and isinstance(cat_pt, str):
            category_map[cat_pt] = str(cat_en) if cat_en else None

    if "product_category_name" in df_products.columns:
        for cat in df_products["product_category_name"].dropna().unique():
            cat_clean = sanitize_val(cat)
            if (
                cat_clean
                and isinstance(cat_clean, str)
                and cat_clean not in category_map
            ):
                category_map[cat_clean] = None

    return [(cat, en) for cat, en in sorted(category_map.items())]


def prepare_customers(
    df: pd.DataFrame,
) -> list[tuple[str, str, str | None, str | None, str | None]]:
    """Transform customers dataset rows into tuples."""
    records: list[tuple[str, str, str | None, str | None, str | None]] = []
    for _, row in df.iterrows():
        zip_clean = sanitize_val(row["customer_zip_code_prefix"])
        city_clean = sanitize_val(row["customer_city"])
        state_clean = sanitize_val(row["customer_state"])
        records.append(
            (
                str(row["customer_id"]),
                str(row["customer_unique_id"]),
                str(zip_clean) if zip_clean is not None else None,
                str(city_clean) if city_clean is not None else None,
                str(state_clean) if state_clean is not None else None,
            )
        )
    return records


def prepare_sellers(
    df: pd.DataFrame,
) -> list[tuple[str, str | None, str | None, str | None]]:
    """Transform sellers dataset rows into tuples."""
    records: list[tuple[str, str | None, str | None, str | None]] = []
    for _, row in df.iterrows():
        zip_clean = sanitize_val(row["seller_zip_code_prefix"])
        city_clean = sanitize_val(row["seller_city"])
        state_clean = sanitize_val(row["seller_state"])
        records.append(
            (
                str(row["seller_id"]),
                str(zip_clean) if zip_clean is not None else None,
                str(city_clean) if city_clean is not None else None,
                str(state_clean) if state_clean is not None else None,
            )
        )
    return records


def prepare_products(
    df: pd.DataFrame,
) -> list[
    tuple[
        str,
        str | None,
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
        int | None,
    ]
]:
    """Transform products dataset rows into tuples with standardized column names."""
    records: list[
        tuple[
            str,
            str | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
        ]
    ] = []
    for _, row in df.iterrows():
        name_len = row.get("product_name_length", row.get("product_name_lenght"))
        desc_len = row.get(
            "product_description_length", row.get("product_description_lenght")
        )
        cat_clean = sanitize_val(row.get("product_category_name"))

        records.append(
            (
                str(row["product_id"]),
                str(cat_clean) if cat_clean is not None else None,
                to_optional_int(name_len),
                to_optional_int(desc_len),
                to_optional_int(row.get("product_photos_qty")),
                to_optional_int(row.get("product_weight_g")),
                to_optional_int(row.get("product_length_cm")),
                to_optional_int(row.get("product_height_cm")),
                to_optional_int(row.get("product_width_cm")),
            )
        )
    return records


def prepare_orders(
    df: pd.DataFrame,
) -> list[
    tuple[
        str,
        str,
        str,
        datetime,
        datetime | None,
        datetime | None,
        datetime | None,
        datetime,
    ]
]:
    """Transform orders dataset rows into tuples with parsed timestamps."""
    records: list[
        tuple[
            str,
            str,
            str,
            datetime,
            datetime | None,
            datetime | None,
            datetime | None,
            datetime,
        ]
    ] = []
    for _, row in df.iterrows():
        purchase_ts = to_optional_datetime(row["order_purchase_timestamp"])
        estimated_ts = to_optional_datetime(row["order_estimated_delivery_date"])

        if purchase_ts is None or estimated_ts is None:
            continue

        records.append(
            (
                str(row["order_id"]),
                str(row["customer_id"]),
                str(row["order_status"]),
                purchase_ts,
                to_optional_datetime(row.get("order_approved_at")),
                to_optional_datetime(row.get("order_delivered_carrier_date")),
                to_optional_datetime(row.get("order_delivered_customer_date")),
                estimated_ts,
            )
        )
    return records


def prepare_order_items(
    df: pd.DataFrame,
) -> list[tuple[str, int, str, str, datetime, float, float]]:
    """Transform order items dataset rows into tuples."""
    records: list[tuple[str, int, str, str, datetime, float, float]] = []
    for _, row in df.iterrows():
        ship_date = to_optional_datetime(row["shipping_limit_date"])
        price = to_optional_float(row["price"])
        freight = to_optional_float(row["freight_value"])

        if ship_date is None or price is None or freight is None:
            continue

        records.append(
            (
                str(row["order_id"]),
                int(row["order_item_id"]),
                str(row["product_id"]),
                str(row["seller_id"]),
                ship_date,
                price,
                freight,
            )
        )
    return records


def prepare_payments(
    df: pd.DataFrame,
) -> list[tuple[str, int, str, int, float]]:
    """Transform order payments dataset rows into tuples."""
    records: list[tuple[str, int, str, int, float]] = []
    for _, row in df.iterrows():
        val = to_optional_float(row["payment_value"])
        if val is None:
            continue

        records.append(
            (
                str(row["order_id"]),
                int(row["payment_sequential"]),
                str(row["payment_type"]),
                int(row.get("payment_installments", 1)),
                val,
            )
        )
    return records


def prepare_reviews(
    df: pd.DataFrame,
) -> list[tuple[str, str, int, str | None, str | None, datetime, datetime]]:
    """Transform order reviews dataset rows into tuples, deduplicating composite PKs."""
    records: list[tuple[str, str, int, str | None, str | None, datetime, datetime]] = []
    seen_keys: set[tuple[str, str]] = set()

    for _, row in df.iterrows():
        rev_id = str(row["review_id"])
        order_id = str(row["order_id"])
        key = (rev_id, order_id)

        if key in seen_keys:
            continue
        seen_keys.add(key)

        created_ts = to_optional_datetime(row["review_creation_date"])
        answered_ts = to_optional_datetime(row["review_answer_timestamp"])

        if created_ts is None:
            continue
        if answered_ts is None:
            answered_ts = created_ts

        title_clean = sanitize_val(row.get("review_comment_title"))
        msg_clean = sanitize_val(row.get("review_comment_message"))

        records.append(
            (
                rev_id,
                order_id,
                int(row["review_score"]),
                str(title_clean) if title_clean is not None else None,
                str(msg_clean) if msg_clean is not None else None,
                created_ts,
                answered_ts,
            )
        )
    return records


# -----------------------------------------------------------------------------
# Database Ingestion Operations
# -----------------------------------------------------------------------------

INSERT_QUERIES: dict[str, str] = {
    "product_categories": """
        INSERT INTO product_categories (
            product_category_name, product_category_name_english
        )
        VALUES (%s, %s)
        ON CONFLICT (product_category_name) DO NOTHING;
    """,
    "customers": """
        INSERT INTO customers (
            customer_id, customer_unique_id, customer_zip_code_prefix,
            customer_city, customer_state
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (customer_id) DO NOTHING;
    """,
    "sellers": """
        INSERT INTO sellers (
            seller_id, seller_zip_code_prefix, seller_city, seller_state
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (seller_id) DO NOTHING;
    """,
    "products": """
        INSERT INTO products (
            product_id, product_category_name, product_name_length,
            product_description_length, product_photos_qty, product_weight_g,
            product_length_cm, product_height_cm, product_width_cm
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id) DO NOTHING;
    """,
    "orders": """
        INSERT INTO orders (
            order_id, customer_id, order_status, order_purchase_timestamp,
            order_approved_at, order_delivered_carrier_date,
            order_delivered_customer_date, order_estimated_delivery_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (order_id) DO NOTHING;
    """,
    "order_items": """
        INSERT INTO order_items (
            order_id, order_item_id, product_id, seller_id,
            shipping_limit_date, price, freight_value
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (order_id, order_item_id) DO NOTHING;
    """,
    "payments": """
        INSERT INTO payments (
            order_id, payment_sequential, payment_type,
            payment_installments, payment_value
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (order_id, payment_sequential) DO NOTHING;
    """,
    "reviews": """
        INSERT INTO reviews (
            review_id, order_id, review_score, review_comment_title,
            review_comment_message, review_creation_date, review_answer_timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id, order_id) DO NOTHING;
    """,
}


def truncate_olist_tables(cur: psycopg.Cursor) -> None:
    """Clear all Olist tables in cascade before reload (preserves datasets)."""
    cur.execute(
        """
        TRUNCATE TABLE
            reviews,
            payments,
            order_items,
            orders,
            products,
            sellers,
            customers,
            product_categories
        CASCADE;
        """
    )


def batch_insert(
    cur: psycopg.Cursor, query: str, rows: list[tuple[Any, ...]], batch_size: int = 5000
) -> None:
    """Insert data rows in parameterized batches using executemany."""
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        cur.executemany(query, batch)


def fetch_table_counts(cur: psycopg.Cursor) -> dict[str, int]:
    """Query actual row counts from PostgreSQL for all 8 Olist tables."""
    counts = {}
    for table in LOAD_ORDER:
        cur.execute(f"SELECT count(*) FROM {table};")
        row = cur.fetchone()
        counts[table] = row[0] if row else 0
    return counts


def run_ingestion() -> None:
    """Execute the end-to-end Olist data ingestion pipeline."""
    print("==================================================")
    print("RootCause AI - Olist Data Ingestion Pipeline")
    print("==================================================")

    # 1. Locate Archive
    zip_path = find_olist_zip()
    print(f"Reading Olist ZIP: {zip_path}")
    print("--------------------------------------------------")

    # 2. Extract DataFrames
    with zipfile.ZipFile(zip_path, "r") as z:
        df_trans = read_csv_from_zip(z, "product_category_name_translation.csv")
        df_cust = read_csv_from_zip(z, "olist_customers_dataset.csv")
        df_sellers = read_csv_from_zip(z, "olist_sellers_dataset.csv")
        df_prods = read_csv_from_zip(z, "olist_products_dataset.csv")
        df_orders = read_csv_from_zip(z, "olist_orders_dataset.csv")
        df_items = read_csv_from_zip(z, "olist_order_items_dataset.csv")
        df_payments = read_csv_from_zip(z, "olist_order_payments_dataset.csv")
        df_reviews = read_csv_from_zip(z, "olist_order_reviews_dataset.csv")

    # 3. Clean and Transform Records
    print("Transforming & Validating Datasets...")
    records_map: dict[str, list[tuple[Any, ...]]] = {
        "product_categories": prepare_product_categories(df_trans, df_prods),
        "customers": prepare_customers(df_cust),
        "sellers": prepare_sellers(df_sellers),
        "products": prepare_products(df_prods),
        "orders": prepare_orders(df_orders),
        "order_items": prepare_order_items(df_items),
        "payments": prepare_payments(df_payments),
        "reviews": prepare_reviews(df_reviews),
    }

    for table in LOAD_ORDER:
        print(f"  [OK] {table:<20}: {len(records_map[table]):>7,d} rows ready")

    print("\nConnecting to Supabase PostgreSQL...")
    settings = get_settings()

    with psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        connect_timeout=15,
    ) as conn:
        with conn.cursor() as cur:
            # 4. Truncate existing Olist data in transaction
            print("Clearing previous Olist data (idempotent reload)...")
            truncate_olist_tables(cur)

            # 5. Insert in foreign-key order
            print("Loading tables into Supabase...")
            for table in LOAD_ORDER:
                query = INSERT_QUERIES[table]
                data = records_map[table]
                batch_insert(cur, query, data)
                print(f"  [OK] {table} loaded ({len(data):,d} rows)")

            conn.commit()

            # 6. Verify row counts in PostgreSQL
            print("\nVerifying database row counts:")
            counts = fetch_table_counts(cur)
            print("--------------------------------------------------")
            print(f"{'Table Name':<25} {'Rows in DB':>15}")
            print("--------------------------------------------------")
            for table, count in counts.items():
                print(f"{table:<25} {count:>15,d}")
            print("--------------------------------------------------")

    print("\nData ingestion completed successfully.")


if __name__ == "__main__":
    run_ingestion()
