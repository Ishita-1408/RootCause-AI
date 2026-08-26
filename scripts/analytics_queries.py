"""RootCause AI - Reusable Analytical SQL Queries & KPI Engine.

This module encapsulates heavily-commented, deterministic SQL queries for
calculating business metrics, cohort behavior, fulfillment operations, customer
satisfaction, and data quality checks from the Olist relational dataset.

CRITICAL ARCHITECTURE & REVENUE GRAIN RULE:
- Grain of `order_items`: 1 row per product item in an order.
- Grain of `payments`: 1 row per payment tender split.
- Direct joins between `order_items` and `payments` without prior aggregation
  cause an (N x M) Cartesian product that silently multiplies revenue.
- All queries in this module strictly pre-aggregate line items or tenders
  before joining across grains.
"""

from typing import Any

import pandas as pd
import psycopg
from psycopg.rows import dict_row

# -----------------------------------------------------------------------------
# 1. Overall Business KPIs Query
# -----------------------------------------------------------------------------
QUERY_OVERALL_BUSINESS_KPIS = """
-- ============================================================================
-- KPI 1: High-Level Platform Overview & Core Economics
-- ============================================================================
WITH order_summary AS (
    SELECT
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS total_customer_transactions,
        COUNT(DISTINCT CASE 
            WHEN order_status = 'delivered' THEN order_id 
        END) AS delivered_orders,
        COUNT(DISTINCT CASE 
            WHEN order_status = 'canceled' THEN order_id 
        END) AS canceled_orders
    FROM orders
),
item_summary AS (
    SELECT
        COUNT(DISTINCT seller_id) AS total_sellers,
        COUNT(DISTINCT product_id) AS total_products,
        COALESCE(SUM(price), 0) AS total_revenue,
        COALESCE(SUM(freight_value), 0) AS total_freight,
        COUNT(DISTINCT order_id) AS orders_with_items
    FROM order_items
),
customer_summary AS (
    SELECT
        COUNT(DISTINCT customer_unique_id) AS total_unique_customers
    FROM customers
),
review_summary AS (
    SELECT
        AVG(review_score) AS avg_review_score,
        COUNT(*) AS total_reviews
    FROM reviews
)
SELECT
    os.total_orders,
    cs.total_unique_customers AS total_customers,
    its.total_sellers,
    its.total_products,
    its.total_revenue,
    CASE 
        WHEN its.orders_with_items > 0 
        THEN its.total_revenue / its.orders_with_items 
        ELSE 0 
    END AS average_order_value,
    its.total_freight,
    rs.avg_review_score,
    (
        os.canceled_orders::NUMERIC / NULLIF(os.total_orders, 0)
    ) * 100 AS cancellation_rate_pct,
    (
        os.delivered_orders::NUMERIC / NULLIF(os.total_orders, 0)
    ) * 100 AS delivered_rate_pct
FROM order_summary os
CROSS JOIN item_summary its
CROSS JOIN customer_summary cs
CROSS JOIN review_summary rs;
"""

# -----------------------------------------------------------------------------
# 2. Monthly Sales & Trend Analysis Query
# -----------------------------------------------------------------------------
QUERY_MONTHLY_SALES_ANALYSIS = """
-- ============================================================================
-- KPI 2: Monthly Sales, Order Volume, AOV, and Delivery Progression
-- ============================================================================
WITH monthly_order_headers AS (
    SELECT
        TO_CHAR(order_purchase_timestamp, 'YYYY-MM') AS year_month,
        COUNT(order_id) AS total_orders,
        COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN order_status = 'canceled' THEN 1 END) AS canceled_orders
    FROM orders
    GROUP BY TO_CHAR(order_purchase_timestamp, 'YYYY-MM')
),
monthly_item_revenue AS (
    SELECT
        TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM') AS year_month,
        COUNT(DISTINCT o.order_id) AS orders_with_revenue,
        SUM(oi.price) AS monthly_revenue,
        SUM(oi.freight_value) AS monthly_freight
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM')
)
SELECT
    moh.year_month,
    moh.total_orders,
    COALESCE(mir.monthly_revenue, 0) AS revenue,
    CASE 
        WHEN COALESCE(mir.orders_with_revenue, 0) > 0 
        THEN mir.monthly_revenue / mir.orders_with_revenue
        ELSE 0
    END AS average_order_value,
    COALESCE(mir.monthly_freight, 0) AS freight_value,
    moh.delivered_orders,
    moh.canceled_orders
FROM monthly_order_headers moh
LEFT JOIN monthly_item_revenue mir ON moh.year_month = mir.year_month
ORDER BY moh.year_month ASC;
"""

# -----------------------------------------------------------------------------
# 3. Product Category Analysis Query (Top 10 by Revenue)
# -----------------------------------------------------------------------------
QUERY_PRODUCT_CATEGORY_ANALYSIS = """
-- ============================================================================
-- KPI 3: Category Performance & Customer Satisfaction
-- ============================================================================
WITH item_categories AS (
    SELECT
        oi.order_id,
        oi.product_id,
        oi.price,
        COALESCE(
            pc.product_category_name_english,
            p.product_category_name,
            'uncategorized'
        ) AS category_name
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_categories pc 
        ON p.product_category_name = pc.product_category_name
),
order_reviews_agg AS (
    SELECT
        order_id,
        AVG(review_score) AS order_review_score
    FROM reviews
    GROUP BY order_id
)
SELECT
    ic.category_name,
    SUM(ic.price) AS total_revenue,
    COUNT(DISTINCT ic.order_id) AS total_orders,
    SUM(ic.price) / NULLIF(COUNT(DISTINCT ic.order_id), 0) AS average_order_value,
    COALESCE(AVG(ora.order_review_score), 0) AS average_review_score
FROM item_categories ic
LEFT JOIN order_reviews_agg ora ON ic.order_id = ora.order_id
GROUP BY ic.category_name
ORDER BY total_revenue DESC
LIMIT 10;
"""

# -----------------------------------------------------------------------------
# 4. Seller Performance Analysis Query (Top 10 by Revenue)
# -----------------------------------------------------------------------------
QUERY_SELLER_ANALYSIS = """
-- ============================================================================
-- KPI 4: Seller Revenue, Fulfillment SLAs, and Quality Metrics
-- ============================================================================
WITH seller_item_fulfillment AS (
    SELECT
        oi.seller_id,
        oi.order_id,
        oi.price,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        CASE 
            WHEN o.order_delivered_customer_date IS NOT NULL 
                 AND o.order_delivered_customer_date > o.order_estimated_delivery_date 
            THEN 1
            ELSE 0
        END AS is_late,
        CASE 
            WHEN o.order_delivered_customer_date IS NOT NULL THEN 1 
            ELSE 0 
        END AS is_delivered
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
),
seller_reviews AS (
    SELECT
        oi.seller_id,
        AVG(r.review_score) AS seller_avg_review
    FROM order_items oi
    JOIN reviews r ON oi.order_id = r.order_id
    GROUP BY oi.seller_id
)
SELECT
    sif.seller_id,
    COALESCE(s.seller_city, 'Unknown') AS seller_city,
    COALESCE(s.seller_state, 'NA') AS seller_state,
    SUM(sif.price) AS total_revenue,
    COUNT(DISTINCT sif.order_id) AS total_orders,
    SUM(sif.price) / NULLIF(COUNT(DISTINCT sif.order_id), 0) AS average_order_value,
    COALESCE(sr.seller_avg_review, 0) AS average_review_score,
    (
        SUM(sif.is_late)::NUMERIC / 
        NULLIF(SUM(sif.is_delivered), 0)
    ) * 100 AS late_delivery_pct
FROM seller_item_fulfillment sif
JOIN sellers s ON sif.seller_id = s.seller_id
LEFT JOIN seller_reviews sr ON sif.seller_id = sr.seller_id
GROUP BY sif.seller_id, s.seller_city, s.seller_state, sr.seller_avg_review
ORDER BY total_revenue DESC
LIMIT 10;
"""

# -----------------------------------------------------------------------------
# 5. Customer Loyalty & Spend Analysis Query
# -----------------------------------------------------------------------------
QUERY_CUSTOMER_ANALYSIS = """
-- ============================================================================
-- KPI 5: Customer Retention, Cohort Order Frequency, and Lifetime Spend
-- ============================================================================
WITH customer_order_totals AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        COALESCE(SUM(oi.price), 0) AS total_spend
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN (
        SELECT order_id, SUM(price) AS price
        FROM order_items
        GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS total_unique_customers,
    COUNT(CASE WHEN order_count > 1 THEN 1 END) AS repeat_customers,
    COUNT(CASE WHEN order_count = 1 THEN 1 END) AS one_time_customers,
    (
        COUNT(CASE WHEN order_count > 1 THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0)
    ) * 100 AS repeat_customer_pct,
    AVG(order_count) AS avg_orders_per_customer,
    AVG(total_spend) AS avg_customer_spend
FROM customer_order_totals;
"""

# -----------------------------------------------------------------------------
# 6. Delivery & Operational Efficiency Query
# -----------------------------------------------------------------------------
QUERY_DELIVERY_OPERATIONS = """
-- ============================================================================
-- KPI 6: Logistics Performance, Lead Times, and SLA Compliance
-- ============================================================================
SELECT
    COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) AS delivered_orders_count,
    AVG(
        EXTRACT(EPOCH FROM (
            order_delivered_customer_date - order_purchase_timestamp
        )) / 86400.0
    ) FILTER (WHERE order_delivered_customer_date IS NOT NULL) AS avg_delivery_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (
            order_delivered_customer_date - order_purchase_timestamp
        )) / 86400.0
    ) FILTER (WHERE order_delivered_customer_date IS NOT NULL) AS median_delivery_days,
    (
        COUNT(CASE 
            WHEN order_delivered_customer_date > order_estimated_delivery_date 
            THEN 1 
        END)::NUMERIC /
        NULLIF(COUNT(CASE 
            WHEN order_delivered_customer_date IS NOT NULL 
            THEN 1 
        END), 0)
    ) * 100 AS late_delivery_pct,
    AVG(
        EXTRACT(EPOCH FROM (
            order_estimated_delivery_date - order_delivered_customer_date
        )) / 86400.0
    ) FILTER (WHERE order_delivered_customer_date IS NOT NULL) 
        AS avg_days_early_vs_estimated,
    (
        COUNT(CASE WHEN order_status = 'canceled' THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0)
    ) * 100 AS cancellation_pct
FROM orders;
"""

# -----------------------------------------------------------------------------
# 7. Customer Reviews & Sentiment Analysis Query
# -----------------------------------------------------------------------------
QUERY_REVIEW_SATISFACTION = """
-- ============================================================================
-- KPI 7: Review Distribution, Revenue by Rating, and Delivery Correlation
-- ============================================================================
WITH order_deliveries AS (
    SELECT
        order_id,
        EXTRACT(EPOCH FROM (
            order_delivered_customer_date - order_purchase_timestamp
        )) / 86400.0 AS delivery_days
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
),
order_revenue AS (
    SELECT
        order_id,
        SUM(price) AS revenue
    FROM order_items
    GROUP BY order_id
),
total_reviews_count AS (
    SELECT COUNT(*) AS total_count FROM reviews
)
SELECT
    r.review_score,
    COUNT(r.review_id) AS total_reviews,
    (
        COUNT(r.review_id)::NUMERIC / 
        (SELECT total_count FROM total_reviews_count)
    ) * 100 AS pct_of_total_reviews,
    COALESCE(SUM(orev.revenue), 0) AS total_associated_revenue,
    AVG(od.delivery_days) AS avg_delivery_days
FROM reviews r
LEFT JOIN order_deliveries od ON r.order_id = od.order_id
LEFT JOIN order_revenue orev ON r.order_id = orev.order_id
GROUP BY r.review_score
ORDER BY r.review_score ASC;
"""

# -----------------------------------------------------------------------------
# 8. Data Quality & Anomaly Checks Query
# -----------------------------------------------------------------------------
QUERY_DATA_QUALITY_CHECKS = """
-- ============================================================================
-- Data Quality Auditing: NULLs, Orphan Records, and Range Invariants
-- ============================================================================
SELECT
    (SELECT COUNT(*) FROM orders 
     WHERE order_id IS NULL OR customer_id IS NULL) AS orders_null_keys,
    (SELECT COUNT(*) FROM order_items 
     WHERE order_id IS NULL OR product_id IS NULL) AS items_null_keys,
    (SELECT COUNT(*) FROM orders o 
     LEFT JOIN order_items oi ON o.order_id = oi.order_id 
     WHERE oi.order_id IS NULL) AS orders_without_items,
    (SELECT COUNT(*) FROM orders o 
     LEFT JOIN payments p ON o.order_id = p.order_id 
     WHERE p.order_id IS NULL) AS orders_without_payments,
    (SELECT COUNT(*) FROM orders o 
     LEFT JOIN reviews r ON o.order_id = r.order_id 
     WHERE r.order_id IS NULL) AS orders_without_reviews,
    (SELECT COUNT(*) FROM products 
     WHERE product_category_name IS NULL) AS products_without_category,
    (SELECT COUNT(*) FROM order_items 
     WHERE price < 0 OR freight_value < 0) AS negative_price_items,
    (SELECT COUNT(*) FROM payments 
     WHERE payment_value < 0) AS negative_payments,
    (SELECT COUNT(*) FROM orders 
     WHERE order_delivered_customer_date < order_purchase_timestamp) 
     AS invalid_delivery_dates,
    (SELECT COUNT(*) FROM orders 
     WHERE order_status NOT IN (
        'delivered', 'shipped', 'canceled', 'unavailable',
        'invoiced', 'processing', 'created', 'approved'
     )) AS unexpected_order_statuses;
"""

# -----------------------------------------------------------------------------
# Execution Helper Functions
# -----------------------------------------------------------------------------


def run_query_as_dict(conn: psycopg.Connection, query: str) -> list[dict[str, Any]]:
    """Execute a query and return rows as dictionaries."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def run_query_as_dataframe(conn: psycopg.Connection, query: str) -> pd.DataFrame:
    """Execute a query and return rows as a pandas DataFrame."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query)
        rows = cur.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([dict(row) for row in rows])
