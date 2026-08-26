"""RootCause AI - Analytical Marts Builder & Verifier.

Rebuilds all Phase 4A analytical tables and views in Supabase PostgreSQL inside an
atomic database transaction:
1. `fact_order_analytics` (Grain: 1 row per order_id)
2. `fact_daily_kpis`      (Grain: 1 row per date x category)
3. `analytics_daily_kpis` (View with 7d/30d rolling window metrics)
4. `dim_customer_cohorts` (Grain: 1 row per customer_unique_id)
"""

import sys
from pathlib import Path

import psycopg

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.config import get_settings  # noqa: E402
from scripts.eda_helpers import format_currency_brl  # noqa: E402

MIGRATION_PATH = (
    PROJECT_ROOT / "supabase" / "migrations" / "003_create_analytical_marts.sql"
)


def verify_order_facts(cur: psycopg.Cursor) -> None:
    """Verify fact_order_analytics row counts and uniqueness."""
    print("\n[1/4] Verifying fact_order_analytics Grain & Row Counts:")
    print("-" * 70)
    cur.execute("SELECT count(*) FROM orders;")
    orders_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT count(*) FROM fact_order_analytics;")
    fact_orders_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute(
        """
        SELECT count(order_id) - count(DISTINCT order_id) 
        FROM fact_order_analytics;
        """
    )
    dupe_orders: int = cur.fetchone()[0]  # type: ignore[index]

    print(f"  Source Orders Count (orders)           : {orders_cnt:>12,d}")
    print(f"  Fact Rows Count (fact_order_analytics) : {fact_orders_cnt:>12,d}")
    print(f"  Duplicate order_id Count               : {dupe_orders:>12,d}")

    if fact_orders_cnt != orders_cnt:
        err = (
            f"Grain violation in fact_order_analytics: "
            f"Expected {orders_cnt:,d}, got {fact_orders_cnt:,d}!"
        )
        raise ValueError(err)
    if dupe_orders > 0:
        err = (
            f"Duplicate order_id found in fact_order_analytics: "
            f"{dupe_orders} duplicates!"
        )
        raise ValueError(err)


def verify_customer_cohorts(cur: psycopg.Cursor) -> None:
    """Verify dim_customer_cohorts row counts and uniqueness."""
    print("\n[2/4] Verifying dim_customer_cohorts Grain & Row Counts:")
    print("-" * 70)
    cur.execute("SELECT count(DISTINCT customer_unique_id) FROM customers;")
    unique_custs_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT count(*) FROM dim_customer_cohorts;")
    cohort_rows_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute(
        """
        SELECT count(customer_unique_id) - count(DISTINCT customer_unique_id) 
        FROM dim_customer_cohorts;
        """
    )
    dupe_custs: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute(
        "SELECT count(*) FROM dim_customer_cohorts WHERE is_repeat_buyer = TRUE;"
    )
    repeat_custs: int = cur.fetchone()[0]  # type: ignore[index]

    print(f"  Unique Human Customers (customers)     : {unique_custs_cnt:>12,d}")
    print(f"  Cohort Rows Count (dim_customer_cohorts): {cohort_rows_cnt:>11,d}")
    print(f"  Duplicate customer_unique_id Count     : {dupe_custs:>12,d}")
    print(f"  Repeat Buyers Count                    : {repeat_custs:>12,d}")

    if cohort_rows_cnt != unique_custs_cnt:
        err = (
            f"Grain violation in dim_customer_cohorts: "
            f"Expected {unique_custs_cnt:,d}, got {cohort_rows_cnt:,d}!"
        )
        raise ValueError(err)
    if dupe_custs > 0:
        err = (
            f"Duplicate customer_unique_id found in dim_customer_cohorts: "
            f"{dupe_custs} duplicates!"
        )
        raise ValueError(err)


def verify_daily_kpis(cur: psycopg.Cursor) -> None:
    """Verify fact_daily_kpis and analytics_daily_kpis view."""
    print("\n[3/4] Verifying fact_daily_kpis & analytics_daily_kpis View:")
    print("-" * 70)
    cur.execute("SELECT count(*) FROM fact_daily_kpis;")
    daily_kpis_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT count(*) FROM analytics_daily_kpis;")
    view_rows_cnt: int = cur.fetchone()[0]  # type: ignore[index]

    print(f"  Daily Category KPI Rows (fact_daily_kpis): {daily_kpis_cnt:>10,d}")
    print(f"  Daily Analytics View Rows (analytics_daily_kpis): {view_rows_cnt:>6,d}")

    if daily_kpis_cnt == 0 or view_rows_cnt != daily_kpis_cnt:
        raise ValueError("fact_daily_kpis or analytics_daily_kpis check failed!")


def reconcile_revenue(cur: psycopg.Cursor) -> None:
    """Reconcile GMV totals across all analytical layers."""
    print("\n[4/4] Cross-Mart Revenue Conservation Reconciliation:")
    print("-" * 70)
    cur.execute("SELECT SUM(price) FROM order_items;")
    raw_items_gmv = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT SUM(order_merchandise_revenue) FROM fact_order_analytics;")
    fact_orders_gmv = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT SUM(total_gmv) FROM fact_daily_kpis;")
    daily_kpis_gmv = cur.fetchone()[0]  # type: ignore[index]

    cur.execute("SELECT SUM(lifetime_spend) FROM dim_customer_cohorts;")
    cohorts_gmv = cur.fetchone()[0]  # type: ignore[index]

    raw_str = format_currency_brl(raw_items_gmv)
    fact_str = format_currency_brl(fact_orders_gmv)
    kpis_str = format_currency_brl(daily_kpis_gmv)
    coh_str = format_currency_brl(cohorts_gmv)

    print(f"  Raw Items GMV (order_items)            : {raw_str:>18}")
    print(f"  Fact Order GMV (fact_order_analytics)  : {fact_str:>18}")
    print(f"  Daily KPIs GMV (fact_daily_kpis)       : {kpis_str:>18}")
    print(f"  Customer Cohorts GMV (dim_cust_cohorts): {coh_str:>18}")

    if not (raw_items_gmv == fact_orders_gmv == daily_kpis_gmv == cohorts_gmv):
        raise ValueError(
            "CRITICAL REVENUE ERROR: GMV totals do not match across marts!"
        )

    print("  [OK] Revenue Conservation Verified: 100% exact match across all marts.")


def build_analytical_marts() -> None:
    """Rebuild all analytical marts inside an atomic transaction."""
    print("=" * 70)
    print(" ROOTCAUSE AI - BUILDING PHASE 4A ANALYTICAL MARTS")
    print("=" * 70)

    if not MIGRATION_PATH.exists():
        raise FileNotFoundError(f"Migration file not found: {MIGRATION_PATH}")

    with open(MIGRATION_PATH, encoding="utf-8") as f:
        migration_sql = f.read()

    settings = get_settings()
    print("Connecting to Supabase PostgreSQL...")

    with psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        connect_timeout=25,
    ) as conn:
        try:
            with conn.cursor() as cur:
                print("Executing 003_create_analytical_marts.sql in transaction...")
                cur.execute(migration_sql)
                print("  [OK] SQL statements executed successfully.")

                verify_order_facts(cur)
                verify_customer_cohorts(cur)
                verify_daily_kpis(cur)
                reconcile_revenue(cur)

            conn.commit()
            print("\n" + "=" * 70)
            print(" ALL ANALYTICAL MARTS BUILT & COMMITTED WITH 100% INTEGRITY")
            print("=" * 70)
        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR] Transaction rolled back due to error: {e}")
            raise


if __name__ == "__main__":
    build_analytical_marts()
