"""RootCause AI - Olist Exploratory Data Analysis & Quality Audit Runner.

Executes analytical KPI queries against Supabase PostgreSQL and displays a
clean, structured terminal report covering platform economics, monthly trends,
top categories, seller performance, logistics, and data quality integrity.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when script is executed directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analytics_queries import (  # noqa: E402
    QUERY_CUSTOMER_ANALYSIS,
    QUERY_DATA_QUALITY_CHECKS,
    QUERY_DELIVERY_OPERATIONS,
    QUERY_MONTHLY_SALES_ANALYSIS,
    QUERY_OVERALL_BUSINESS_KPIS,
    QUERY_PRODUCT_CATEGORY_ANALYSIS,
    QUERY_REVIEW_SATISFACTION,
    QUERY_SELLER_ANALYSIS,
)
from scripts.eda_helpers import (  # noqa: E402
    format_currency_brl,
    format_pct,
    query_df,
)


def print_overall_kpis() -> None:
    """Print high-level platform summary and financial metrics."""
    df_overall = query_df(QUERY_OVERALL_BUSINESS_KPIS)
    if df_overall.empty:
        return
    row = df_overall.iloc[0]
    print("\n1. OVERALL BUSINESS & PLATFORM KPIs")
    print("-" * 70)
    print(f"  Total Orders               : {int(row['total_orders']):>15,d}")
    print(f"  Total Unique Customers     : {int(row['total_customers']):>15,d}")
    print(f"  Total Active Sellers       : {int(row['total_sellers']):>15,d}")
    print(f"  Total Catalog Products     : {int(row['total_products']):>15,d}")
    rev_str = format_currency_brl(row["total_revenue"])
    print(f"  Total Merchandise Revenue  : {rev_str:>15}")
    aov_str = format_currency_brl(row["average_order_value"])
    print(f"  Average Order Value (AOV)  : {aov_str:>15}")
    frt_str = format_currency_brl(row["total_freight"])
    print(f"  Total Freight Revenue      : {frt_str:>15}")
    score_val = float(row["avg_review_score"])
    print(f"  Average Review Score       : {score_val:>14.2f} / 5.0")
    deliv_pct = format_pct(row["delivered_rate_pct"])
    print(f"  Delivered Order Rate       : {deliv_pct:>15}")
    cancel_pct = format_pct(row["cancellation_rate_pct"])
    print(f"  Cancellation Rate          : {cancel_pct:>15}")


def print_customer_cohorts() -> None:
    """Print customer loyalty, retention rates, and lifetime spend."""
    df_cust = query_df(QUERY_CUSTOMER_ANALYSIS)
    if df_cust.empty:
        return
    crow = df_cust.iloc[0]
    print("\n2. CUSTOMER RETENTION & LIFETIME VALUE")
    print("-" * 70)
    print(f"  Total Buyers (Human)       : {int(crow['total_unique_customers']):>15,d}")
    print(f"  One-Time Customers         : {int(crow['one_time_customers']):>15,d}")
    print(f"  Repeat Customers (>1 order): {int(crow['repeat_customers']):>15,d}")
    rep_pct = format_pct(crow["repeat_customer_pct"])
    print(f"  Repeat Customer Rate       : {rep_pct:>15}")
    orders_avg = float(crow["avg_orders_per_customer"])
    print(f"  Avg Orders per Buyer       : {orders_avg:>15.2f}")
    spend_str = format_currency_brl(crow["avg_customer_spend"])
    print(f"  Avg Lifetime Spend         : {spend_str:>15}")


def print_delivery_operations() -> None:
    """Print logistics lead times, delivery delays, and SLA adherence."""
    df_deliv = query_df(QUERY_DELIVERY_OPERATIONS)
    if df_deliv.empty:
        return
    drow = df_deliv.iloc[0]
    print("\n3. FULFILLMENT & LOGISTICS OPERATIONS")
    print("-" * 70)
    print(f"  Delivered Orders Count     : {int(drow['delivered_orders_count']):>15,d}")
    deliv_days = float(drow["avg_delivery_days"])
    print(f"  Average Delivery Time      : {deliv_days:>12.1f} days")
    med_days = float(drow["median_delivery_days"])
    print(f"  Median Delivery Time       : {med_days:>12.1f} days")
    late_pct = format_pct(drow["late_delivery_pct"])
    print(f"  Late Delivery Rate (>Est.) : {late_pct:>15}")
    diff_val = float(drow["avg_days_early_vs_estimated"])
    print(f"  Avg Days Early vs Estimated: {diff_val:>12.1f} days")
    canc_pct = format_pct(drow["cancellation_pct"])
    print(f"  Cancellation Rate          : {canc_pct:>15}")


def print_reviews_satisfaction() -> None:
    """Print customer satisfaction survey breakdown and delivery correlation."""
    df_rev = query_df(QUERY_REVIEW_SATISFACTION)
    if df_rev.empty:
        return
    print("\n4. CUSTOMER SATISFACTION & DELIVERY CORRELATION")
    print("-" * 70)
    col1 = "  Score    Reviews    % Total          Revenue   Avg Deliv"
    print(col1)
    print("  " + "-" * 66)
    for _, r in df_rev.iterrows():
        score_str = f"{int(r['review_score'])} Stars"
        rev_str = format_currency_brl(r["total_associated_revenue"])
        pct_str = format_pct(r["pct_of_total_reviews"])
        deliv_days = float(r["avg_delivery_days"] or 0)
        row_str = (
            f"  {score_str:<7} {int(r['total_reviews']):>10,d} "
            f"{pct_str:>9} {rev_str:>15} {deliv_days:>9.1f} days"
        )
        print(row_str)


def print_top_categories() -> None:
    """Print top 10 product categories by total merchandise revenue."""
    df_cats = query_df(QUERY_PRODUCT_CATEGORY_ANALYSIS)
    if df_cats.empty:
        return
    print("\n5. TOP 10 PRODUCT CATEGORIES BY REVENUE")
    print("-" * 70)
    hdr = f"  {'Category Name':<26} {'Revenue (BRL)':>15} {'Orders':>8} {'AOV':>10}"
    print(hdr)
    print("  " + "-" * 63)
    for _, cat in df_cats.iterrows():
        name = str(cat["category_name"])[:24]
        rev_str = format_currency_brl(cat["total_revenue"])
        aov_str = format_currency_brl(cat["average_order_value"])
        cnt = int(cat["total_orders"])
        print(f"  {name:<26} {rev_str:>15} {cnt:>8,d} {aov_str:>10}")


def print_top_sellers() -> None:
    """Print top 10 marketplace sellers by total merchandise volume."""
    df_sellers = query_df(QUERY_SELLER_ANALYSIS)
    if df_sellers.empty:
        return
    print("\n6. TOP 10 SELLERS BY REVENUE")
    print("-" * 70)
    col1 = "  Seller ID              State        Revenue  Orders  Late%  Rating"
    print(col1)
    print("  " + "-" * 68)
    for _, sel in df_sellers.iterrows():
        s_id = str(sel["seller_id"])[:20]
        st = str(sel["seller_state"])[:5]
        rev_str = format_currency_brl(sel["total_revenue"])
        late_str = format_pct(sel["late_delivery_pct"])
        rating_val = float(sel["average_review_score"])
        row_str = (
            f"  {s_id:<22} {st:<5} {rev_str:>14} "
            f"{int(sel['total_orders']):>7,d} {late_str:>7} {rating_val:>7.2f}"
        )
        print(row_str)


def print_monthly_trends() -> None:
    """Print monthly revenue and order volume progression for 2017-2018."""
    df_monthly = query_df(QUERY_MONTHLY_SALES_ANALYSIS)
    if df_monthly.empty:
        return
    print("\n7. MONTHLY SALES TIMELINE (2017 - 2018 High-Volume Window)")
    print("-" * 70)
    col1 = "  Month        Orders    Revenue (BRL)        AOV  Delivered"
    print(col1)
    print("  " + "-" * 62)
    for _, m in df_monthly.iterrows():
        if str(m["year_month"]) >= "2017-01":
            rev_str = format_currency_brl(m["revenue"])
            aov_str = format_currency_brl(m["average_order_value"])
            row_str = (
                f"  {str(m['year_month']):<10} {int(m['total_orders']):>8,d} "
                f"{rev_str:>16} {aov_str:>10} {int(m['delivered_orders']):>10,d}"
            )
            print(row_str)


def print_data_quality() -> None:
    """Print data quality and referential integrity audit checks."""
    df_dq = query_df(QUERY_DATA_QUALITY_CHECKS)
    if df_dq.empty:
        return
    dq = df_dq.iloc[0]
    print("\n8. DATA QUALITY & INTEGRITY AUDIT")
    print("-" * 70)
    print(f"  Orders with NULL Keys      : {int(dq['orders_null_keys']):>8,d}")
    print(f"  Items with NULL Keys       : {int(dq['items_null_keys']):>8,d}")
    print(f"  Orders without Items       : {int(dq['orders_without_items']):>8,d}")
    print(f"  Orders without Payments    : {int(dq['orders_without_payments']):>8,d}")
    print(f"  Orders without Reviews     : {int(dq['orders_without_reviews']):>8,d}")
    print(f"  Products without Category  : {int(dq['products_without_category']):>8,d}")
    print(f"  Negative Price/Freight     : {int(dq['negative_price_items']):>8,d}")
    print(f"  Negative Payments          : {int(dq['negative_payments']):>8,d}")
    print(f"  Invalid Delivery Dates     : {int(dq['invalid_delivery_dates']):>8,d}")
    print(f"  Unexpected Order Statuses  : {int(dq['unexpected_order_statuses']):>8,d}")


def run_eda_cli() -> None:
    """Run all analytical queries and render the CLI report."""
    print("=" * 70)
    print(" ROOTCAUSE AI - OLIST DATA QUALITY & EXPLORATORY ANALYSIS (EDA)")
    print("=" * 70)

    print_overall_kpis()
    print_customer_cohorts()
    print_delivery_operations()
    print_reviews_satisfaction()
    print_top_categories()
    print_top_sellers()
    print_monthly_trends()
    print_data_quality()

    print("\n" + "=" * 70)
    print(" DATA QUALITY & EDA REPORT COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_eda_cli()
