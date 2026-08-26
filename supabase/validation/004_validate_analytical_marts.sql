-- ============================================================================
-- Validation Script: 004_validate_analytical_marts.sql
-- Description: Diagnostic verification queries for Phase 4A analytical marts:
--              1. fact_order_analytics
--              2. fact_daily_kpis
--              3. analytics_daily_kpis (view)
--              4. dim_customer_cohorts
--
-- Instructions: Run this script in Supabase SQL Editor to audit table integrity.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Check for Duplicate order_id in fact_order_analytics (Expected: 0)
-- ----------------------------------------------------------------------------
SELECT 
    '1. Duplicate order_id in fact_order_analytics' AS test_name,
    COUNT(order_id) - COUNT(DISTINCT order_id) AS metric_value,
    CASE 
        WHEN COUNT(order_id) - COUNT(DISTINCT order_id) = 0 THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status
FROM fact_order_analytics;

-- ----------------------------------------------------------------------------
-- 2. Check for Duplicate customer_unique_id in dim_customer_cohorts (Expected: 0)
-- ----------------------------------------------------------------------------
SELECT 
    '2. Duplicate customer_unique_id in dim_customer_cohorts' AS test_name,
    COUNT(customer_unique_id) - COUNT(DISTINCT customer_unique_id) AS metric_value,
    CASE 
        WHEN COUNT(customer_unique_id) - COUNT(DISTINCT customer_unique_id) = 0 THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status
FROM dim_customer_cohorts;

-- ----------------------------------------------------------------------------
-- 3. Check for NULL/Invalid Critical Fields in fact_order_analytics (Expected: 0)
-- ----------------------------------------------------------------------------
SELECT 
    '3. NULLs in Critical Identity/Timestamp Columns' AS test_name,
    COUNT(*) FILTER (
        WHERE order_id IS NULL 
           OR customer_id IS NULL 
           OR customer_unique_id IS NULL 
           OR order_status IS NULL 
           OR order_purchase_timestamp IS NULL 
           OR order_estimated_delivery_date IS NULL
    ) AS metric_value,
    CASE 
        WHEN COUNT(*) FILTER (
            WHERE order_id IS NULL 
               OR customer_id IS NULL 
               OR customer_unique_id IS NULL 
               OR order_status IS NULL 
               OR order_purchase_timestamp IS NULL 
               OR order_estimated_delivery_date IS NULL
        ) = 0 THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status
FROM fact_order_analytics;

-- ----------------------------------------------------------------------------
-- 4. Check Delivery Lead-Time Bounds & Anomalies
-- ----------------------------------------------------------------------------
SELECT 
    '4. Negative Delivery Durations Audit' AS metric_description,
    COUNT(*) FILTER (WHERE total_delivery_days < 0) AS negative_delivery_days_count,
    COUNT(*) FILTER (WHERE seller_dispatch_days < 0) AS negative_dispatch_days_count,
    ROUND(MIN(total_delivery_days), 2) AS min_delivery_days,
    ROUND(MAX(total_delivery_days), 2) AS max_delivery_days,
    ROUND(AVG(total_delivery_days), 2) AS avg_delivery_days
FROM fact_order_analytics
WHERE order_delivered_customer_date IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 5. Calculate Late Delivery Rate (% of delivered orders breached SLA)
-- ----------------------------------------------------------------------------
SELECT 
    '5. Fulfillment SLA & Late Delivery Rate' AS metric_description,
    COUNT(*) AS total_delivered_orders,
    COUNT(*) FILTER (WHERE is_late_delivery = TRUE) AS late_orders_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_late_delivery = TRUE) / COUNT(*), 
        2
    ) AS late_delivery_rate_pct
FROM fact_order_analytics
WHERE is_late_delivery IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 6. Total Order Count Invariant (orders vs fact_order_analytics)
-- ----------------------------------------------------------------------------
SELECT 
    '6. Total Order Count Invariant' AS test_name,
    (SELECT COUNT(*) FROM orders) AS raw_orders_count,
    (SELECT COUNT(*) FROM fact_order_analytics) AS fact_orders_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM orders) = (SELECT COUNT(*) FROM fact_order_analytics) 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status;

-- ----------------------------------------------------------------------------
-- 7. Cross-Mart Total GMV Reconciliation (Expected exact match: R$ 13,591,643.70)
-- ----------------------------------------------------------------------------
SELECT 
    '7. Total GMV Reconciliation' AS test_name,
    (SELECT SUM(price)::NUMERIC(12,2) FROM order_items) AS raw_items_gmv,
    (SELECT SUM(order_merchandise_revenue)::NUMERIC(12,2) FROM fact_order_analytics) AS fact_orders_gmv,
    (SELECT SUM(total_gmv)::NUMERIC(12,2) FROM fact_daily_kpis) AS daily_kpis_gmv,
    (SELECT SUM(lifetime_spend)::NUMERIC(12,2) FROM dim_customer_cohorts) AS cohorts_gmv,
    CASE 
        WHEN (SELECT SUM(price)::NUMERIC(12,2) FROM order_items) = 
             (SELECT SUM(order_merchandise_revenue)::NUMERIC(12,2) FROM fact_order_analytics)
         AND (SELECT SUM(order_merchandise_revenue)::NUMERIC(12,2) FROM fact_order_analytics) = 
             (SELECT SUM(total_gmv)::NUMERIC(12,2) FROM fact_daily_kpis)
         AND (SELECT SUM(total_gmv)::NUMERIC(12,2) FROM fact_daily_kpis) = 
             (SELECT SUM(lifetime_spend)::NUMERIC(12,2) FROM dim_customer_cohorts)
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status;

-- ----------------------------------------------------------------------------
-- 8. Category KPI Slice Summary in fact_daily_kpis
-- ----------------------------------------------------------------------------
SELECT 
    '8. Category KPI Summary' AS metric_description,
    COUNT(DISTINCT product_category_name) AS distinct_categories,
    MIN(kpi_date) AS min_kpi_date,
    MAX(kpi_date) AS max_kpi_date,
    COUNT(*) AS total_daily_category_slices
FROM fact_daily_kpis;

-- ----------------------------------------------------------------------------
-- 9. Repeat Buyer Rate in dim_customer_cohorts
-- ----------------------------------------------------------------------------
SELECT 
    '9. Customer Cohort & Repeat Rate' AS metric_description,
    COUNT(*) AS total_unique_customers,
    COUNT(*) FILTER (WHERE is_repeat_buyer = TRUE) AS repeat_buyers_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_repeat_buyer = TRUE) / COUNT(*), 
        2
    ) AS repeat_buyer_pct
FROM dim_customer_cohorts;
