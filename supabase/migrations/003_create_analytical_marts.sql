-- ============================================================================
-- Migration: 003_create_analytical_marts.sql
-- Description: Creates the Phase 4A Analytical Layer for RootCause AI:
--              1. fact_order_analytics (Grain: 1 row per order_id)
--              2. fact_daily_kpis      (Grain: 1 row per date x category)
--              3. analytics_daily_kpis (View: adds 7d/30d rolling GMV)
--              4. dim_customer_cohorts (Grain: 1 row per customer_unique_id)
--
-- ARCHITECTURE FLOW:
-- Raw Olist Tables -> Pre-aggregated Child CTEs -> Fact & Dimension Marts -> Analytical Views
--
-- CRITICAL GRAIN & REVENUE CONSERVATION PRINCIPLES:
-- 1. Raw `order_items` and `payments` are NEVER joined directly without prior
--    aggregation to the order level to prevent Cartesian revenue inflation.
-- 2. Category KPI GMV aggregates item-level price to preserve exact revenue.
-- 3. customer_unique_id (not customer_id) is used for customer lifetime analytics.
-- ============================================================================

-- Drop dependent view and tables cleanly
DROP VIEW IF EXISTS analytics_daily_kpis CASCADE;
DROP TABLE IF EXISTS fact_daily_kpis CASCADE;
DROP TABLE IF EXISTS dim_customer_cohorts CASCADE;
DROP TABLE IF EXISTS fact_order_analytics CASCADE;

-- ============================================================================
-- 1. TABLE: fact_order_analytics
-- Grain: Exactly ONE row per order_id
-- ============================================================================
CREATE TABLE fact_order_analytics (
    -- Identity
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,

    -- Geography
    customer_city TEXT,
    customer_state TEXT,

    -- Order Lifecycle & Timestamps
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ NOT NULL,

    -- Financials & Basket Metrics (from order_items)
    order_merchandise_revenue NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    order_freight_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    order_total_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    freight_to_price_ratio NUMERIC(10, 4),
    item_count INTEGER NOT NULL DEFAULT 0,
    distinct_sellers_count INTEGER NOT NULL DEFAULT 0,

    -- Tender & Payment Details (from payments)
    primary_payment_type TEXT,
    payment_installments_max INTEGER NOT NULL DEFAULT 0,
    total_payment_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,

    -- Delivery Milestones & Durations (Hours / Days)
    approval_lead_hours NUMERIC(10, 2),
    seller_dispatch_days NUMERIC(10, 2),
    carrier_transit_days NUMERIC(10, 2),
    total_delivery_days NUMERIC(10, 2),
    delivery_delay_days NUMERIC(10, 2),
    is_late_delivery BOOLEAN,

    -- Customer Sentiment (from reviews)
    review_score NUMERIC(3, 2),
    review_count INTEGER NOT NULL DEFAULT 0,
    is_negative_review BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for fact_order_analytics
CREATE INDEX idx_fact_order_analytics_cust_uniq 
    ON fact_order_analytics (customer_unique_id);

CREATE INDEX idx_fact_order_analytics_purch_ts 
    ON fact_order_analytics (order_purchase_timestamp);

CREATE INDEX idx_fact_order_analytics_state 
    ON fact_order_analytics (customer_state);

CREATE INDEX idx_fact_order_analytics_status 
    ON fact_order_analytics (order_status);

CREATE INDEX idx_fact_order_analytics_is_late 
    ON fact_order_analytics (is_late_delivery);

-- Population: Grain-Protected Aggregation and Insert
INSERT INTO fact_order_analytics (
    order_id,
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    order_merchandise_revenue,
    order_freight_value,
    order_total_value,
    freight_to_price_ratio,
    item_count,
    distinct_sellers_count,
    primary_payment_type,
    payment_installments_max,
    total_payment_value,
    approval_lead_hours,
    seller_dispatch_days,
    carrier_transit_days,
    total_delivery_days,
    delivery_delay_days,
    is_late_delivery,
    review_score,
    review_count,
    is_negative_review
)
WITH item_agg AS (
    -- 1. Pre-aggregate order items (Grain: 1 row per order_id)
    SELECT
        order_id,
        COALESCE(SUM(price), 0)::NUMERIC(12, 2) AS order_merchandise_revenue,
        COALESCE(SUM(freight_value), 0)::NUMERIC(12, 2) AS order_freight_value,
        COALESCE(SUM(price + freight_value), 0)::NUMERIC(12, 2) AS order_total_value,
        COUNT(order_item_id)::INTEGER AS item_count,
        COUNT(DISTINCT seller_id)::INTEGER AS distinct_sellers_count
    FROM order_items
    GROUP BY order_id
),
payment_ranked AS (
    -- Rank payment tender types by largest value per order
    SELECT
        order_id,
        payment_type,
        payment_value,
        payment_installments,
        ROW_NUMBER() OVER (
            PARTITION BY order_id 
            ORDER BY payment_value DESC, payment_sequential ASC
        ) AS rn
    FROM payments
),
payment_agg AS (
    -- 2. Pre-aggregate payment splits (Grain: 1 row per order_id)
    SELECT
        p.order_id,
        COALESCE(SUM(p.payment_value), 0)::NUMERIC(12, 2) AS total_payment_value,
        MAX(CASE WHEN pr.rn = 1 THEN pr.payment_type END) AS primary_payment_type,
        MAX(p.payment_installments)::INTEGER AS payment_installments_max
    FROM payments p
    LEFT JOIN payment_ranked pr ON p.order_id = pr.order_id AND pr.rn = 1
    GROUP BY p.order_id
),
review_agg AS (
    -- 3. Pre-aggregate customer reviews (Grain: 1 row per order_id)
    SELECT
        order_id,
        ROUND(AVG(review_score), 2)::NUMERIC(3, 2) AS review_score,
        COUNT(review_id)::INTEGER AS review_count,
        BOOL_OR(review_score <= 2) AS is_negative_review
    FROM reviews
    GROUP BY order_id
)
SELECT
    -- Identity & Demographics
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    -- Order lifecycle
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    -- Revenue
    COALESCE(ia.order_merchandise_revenue, 0)::NUMERIC(12, 2) AS order_merchandise_revenue,
    COALESCE(ia.order_freight_value, 0)::NUMERIC(12, 2) AS order_freight_value,
    COALESCE(ia.order_total_value, 0)::NUMERIC(12, 2) AS order_total_value,
    CASE 
        WHEN COALESCE(ia.order_merchandise_revenue, 0) > 0 
        THEN ROUND((ia.order_freight_value / ia.order_merchandise_revenue), 4)
        ELSE NULL 
    END AS freight_to_price_ratio,
    COALESCE(ia.item_count, 0)::INTEGER AS item_count,
    COALESCE(ia.distinct_sellers_count, 0)::INTEGER AS distinct_sellers_count,
    -- Payment
    pa.primary_payment_type,
    COALESCE(pa.payment_installments_max, 0)::INTEGER AS payment_installments_max,
    COALESCE(pa.total_payment_value, 0)::NUMERIC(12, 2) AS total_payment_value,
    -- Logistics & Lead times
    ROUND(
        EXTRACT(EPOCH FROM (o.order_approved_at - o.order_purchase_timestamp)) / 3600.0, 
        2
    )::NUMERIC(10, 2) AS approval_lead_hours,
    ROUND(
        EXTRACT(EPOCH FROM (o.order_delivered_carrier_date - o.order_approved_at)) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS seller_dispatch_days,
    ROUND(
        EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_delivered_carrier_date)) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS carrier_transit_days,
    ROUND(
        EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS total_delivery_days,
    ROUND(
        EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date)) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS delivery_delay_days,
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL 
        THEN (o.order_delivered_customer_date > o.order_estimated_delivery_date)
        ELSE NULL
    END AS is_late_delivery,
    -- Sentiment
    ra.review_score,
    COALESCE(ra.review_count, 0)::INTEGER AS review_count,
    COALESCE(ra.is_negative_review, FALSE) AS is_negative_review
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN item_agg ia ON o.order_id = ia.order_id
LEFT JOIN payment_agg pa ON o.order_id = pa.order_id
LEFT JOIN review_agg ra ON o.order_id = ra.order_id;


-- ============================================================================
-- 2. TABLE: fact_daily_kpis
-- Grain: Exactly ONE row per (kpi_date x product_category_name)
-- ============================================================================
CREATE TABLE fact_daily_kpis (
    kpi_date DATE NOT NULL,
    product_category_name TEXT NOT NULL,

    -- Volume & Fulfillment Funnel
    orders_count INTEGER NOT NULL DEFAULT 0,
    delivered_orders_count INTEGER NOT NULL DEFAULT 0,
    canceled_orders_count INTEGER NOT NULL DEFAULT 0,

    -- Financial Metrics
    total_gmv NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_freight_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    average_order_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,

    -- Logistics SLA
    avg_delivery_lead_days NUMERIC(10, 2),
    late_delivery_rate_pct NUMERIC(5, 2),

    -- Customer Sentiment
    avg_review_score NUMERIC(3, 2),
    negative_review_rate_pct NUMERIC(5, 2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (kpi_date, product_category_name)
);

CREATE INDEX idx_fact_daily_kpis_date ON fact_daily_kpis (kpi_date);
CREATE INDEX idx_fact_daily_kpis_category ON fact_daily_kpis (product_category_name);

INSERT INTO fact_daily_kpis (
    kpi_date,
    product_category_name,
    orders_count,
    delivered_orders_count,
    canceled_orders_count,
    total_gmv,
    total_freight_value,
    average_order_value,
    avg_delivery_lead_days,
    late_delivery_rate_pct,
    avg_review_score,
    negative_review_rate_pct
)
SELECT
    foa.order_purchase_timestamp::DATE AS kpi_date,
    COALESCE(p.product_category_name, 'uncategorized') AS product_category_name,
    COUNT(DISTINCT foa.order_id)::INTEGER AS orders_count,
    COUNT(DISTINCT CASE WHEN foa.order_status = 'delivered' THEN foa.order_id END)::INTEGER AS delivered_orders_count,
    COUNT(DISTINCT CASE WHEN foa.order_status = 'canceled' THEN foa.order_id END)::INTEGER AS canceled_orders_count,
    COALESCE(SUM(oi.price), 0.00)::NUMERIC(12, 2) AS total_gmv,
    COALESCE(SUM(oi.freight_value), 0.00)::NUMERIC(12, 2) AS total_freight_value,
    ROUND(
        COALESCE(SUM(oi.price), 0.00) / NULLIF(COUNT(DISTINCT foa.order_id), 0), 
        2
    )::NUMERIC(12, 2) AS average_order_value,
    ROUND(AVG(foa.total_delivery_days), 2)::NUMERIC(10, 2) AS avg_delivery_lead_days,
    ROUND(
        100.0 * COUNT(CASE WHEN foa.is_late_delivery = TRUE THEN 1 END) / 
        NULLIF(COUNT(CASE WHEN foa.is_late_delivery IS NOT NULL THEN 1 END), 0), 
        2
    )::NUMERIC(5, 2) AS late_delivery_rate_pct,
    ROUND(AVG(foa.review_score), 2)::NUMERIC(3, 2) AS avg_review_score,
    ROUND(
        100.0 * COUNT(CASE WHEN foa.review_score <= 2 THEN 1 END) / 
        NULLIF(COUNT(CASE WHEN foa.review_score IS NOT NULL THEN 1 END), 0), 
        2
    )::NUMERIC(5, 2) AS negative_review_rate_pct
FROM fact_order_analytics foa
JOIN order_items oi ON foa.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY 
    foa.order_purchase_timestamp::DATE, 
    COALESCE(p.product_category_name, 'uncategorized');


-- ============================================================================
-- 3. VIEW: analytics_daily_kpis
-- Purpose: Adds 7d and 30d rolling window metrics on top of physical fact table
-- ============================================================================
CREATE OR REPLACE VIEW analytics_daily_kpis AS
SELECT
    kpi_date,
    product_category_name,
    orders_count,
    delivered_orders_count,
    canceled_orders_count,
    total_gmv,
    total_freight_value,
    average_order_value,
    avg_delivery_lead_days,
    late_delivery_rate_pct,
    avg_review_score,
    negative_review_rate_pct,
    -- 7-Day Rolling Window (partitioned by category, ordered by date)
    ROUND(
        AVG(total_gmv) OVER (
            PARTITION BY product_category_name 
            ORDER BY kpi_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    )::NUMERIC(12, 2) AS rolling_7d_gmv,
    -- 30-Day Rolling Window (partitioned by category, ordered by date)
    ROUND(
        AVG(total_gmv) OVER (
            PARTITION BY product_category_name 
            ORDER BY kpi_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    )::NUMERIC(12, 2) AS rolling_30d_gmv
FROM fact_daily_kpis;


-- ============================================================================
-- 4. TABLE: dim_customer_cohorts
-- Grain: Exactly ONE row per customer_unique_id
-- ============================================================================
CREATE TABLE dim_customer_cohorts (
    customer_unique_id TEXT PRIMARY KEY,
    first_order_date TIMESTAMPTZ NOT NULL,
    first_order_month DATE NOT NULL,
    last_order_date TIMESTAMPTZ NOT NULL,
    lifetime_order_count INTEGER NOT NULL,
    lifetime_spend NUMERIC(12, 2) NOT NULL,
    average_order_value NUMERIC(12, 2) NOT NULL,
    is_repeat_buyer BOOLEAN NOT NULL,
    days_since_last_order NUMERIC(10, 2),
    customer_lifetime_days NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dim_cust_cohorts_month ON dim_customer_cohorts (first_order_month);
CREATE INDEX idx_dim_cust_cohorts_repeat ON dim_customer_cohorts (is_repeat_buyer);

INSERT INTO dim_customer_cohorts (
    customer_unique_id,
    first_order_date,
    first_order_month,
    last_order_date,
    lifetime_order_count,
    lifetime_spend,
    average_order_value,
    is_repeat_buyer,
    days_since_last_order,
    customer_lifetime_days
)
WITH max_ref AS (
    SELECT MAX(order_purchase_timestamp) AS dataset_max_ts FROM fact_order_analytics
)
SELECT
    foa.customer_unique_id,
    MIN(foa.order_purchase_timestamp) AS first_order_date,
    DATE_TRUNC('month', MIN(foa.order_purchase_timestamp))::DATE AS first_order_month,
    MAX(foa.order_purchase_timestamp) AS last_order_date,
    COUNT(foa.order_id)::INTEGER AS lifetime_order_count,
    SUM(foa.order_merchandise_revenue)::NUMERIC(12, 2) AS lifetime_spend,
    ROUND(
        SUM(foa.order_merchandise_revenue) / NULLIF(COUNT(foa.order_id), 0), 
        2
    )::NUMERIC(12, 2) AS average_order_value,
    (COUNT(foa.order_id) > 1) AS is_repeat_buyer,
    ROUND(
        EXTRACT(EPOCH FROM ((SELECT dataset_max_ts FROM max_ref) - MAX(foa.order_purchase_timestamp))) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS days_since_last_order,
    ROUND(
        EXTRACT(EPOCH FROM (MAX(foa.order_purchase_timestamp) - MIN(foa.order_purchase_timestamp))) / 86400.0, 
        2
    )::NUMERIC(10, 2) AS customer_lifetime_days
FROM fact_order_analytics foa
GROUP BY foa.customer_unique_id;
