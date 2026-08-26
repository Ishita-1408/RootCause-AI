"""SQL Query Definitions for the RootCause AI Deterministic Analytical Layer.

Queries target the Phase 4A analytical feature marts (fact_order_analytics,
fact_daily_kpis, dim_customer_cohorts) using parameterized PostgreSQL SQL.
"""

# ============================================================================
# 1. Headline KPIs Summary Query
# ============================================================================
KPI_SUMMARY_SQL = """
WITH period_orders AS (
    SELECT
        foa.*,
        coh.first_order_date
    FROM fact_order_analytics foa
    JOIN dim_customer_cohorts coh 
        ON foa.customer_unique_id = coh.customer_unique_id
    WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
)
SELECT
    -- Revenue
    COALESCE(SUM(merchandise_revenue), 0.00)::FLOAT AS gmv,
    COALESCE(
        SUM(
            CASE 
                WHEN order_status = 'delivered' 
                THEN merchandise_revenue 
                ELSE 0 
            END
        ), 
        0.00
    )::FLOAT AS delivered_gmv,
    CASE 
        WHEN COUNT(order_id) > 0 
        THEN (
            COALESCE(SUM(merchandise_revenue), 0.00) / COUNT(order_id)
        )::FLOAT
        ELSE NULL 
    END AS average_order_value,
    CASE 
        WHEN COUNT(DISTINCT customer_unique_id) > 0 
        THEN (
            COALESCE(SUM(merchandise_revenue), 0.00) 
            / COUNT(DISTINCT customer_unique_id)
        )::FLOAT
        ELSE NULL 
    END AS revenue_per_customer,

    -- Volume
    COUNT(DISTINCT order_id)::INTEGER AS orders_count,
    COUNT(
        DISTINCT CASE WHEN order_status = 'delivered' THEN order_id END
    )::INTEGER AS delivered_orders_count,
    COUNT(
        DISTINCT CASE WHEN order_status = 'canceled' THEN order_id END
    )::INTEGER AS canceled_orders_count,
    COALESCE(SUM(item_count), 0)::INTEGER AS items_sold_count,

    -- Customer
    COUNT(DISTINCT customer_unique_id)::INTEGER AS unique_customers_count,
    COUNT(
        DISTINCT CASE 
            WHEN first_order_date >= %s::TIMESTAMPTZ 
             AND first_order_date < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ 
            THEN customer_unique_id 
        END
    )::INTEGER AS new_customers_count,
    COUNT(
        DISTINCT CASE 
            WHEN order_purchase_timestamp > first_order_date 
            THEN customer_unique_id 
        END
    )::INTEGER AS repeat_customers_count,
    CASE 
        WHEN COUNT(DISTINCT customer_unique_id) > 0 
        THEN (
            100.0 * COUNT(
                DISTINCT CASE 
                    WHEN order_purchase_timestamp > first_order_date 
                    THEN customer_unique_id 
                END
            )
            / COUNT(DISTINCT customer_unique_id)
        )::FLOAT
        ELSE NULL 
    END AS repeat_buyer_rate_pct,

    -- Logistics SLA
    CASE 
        WHEN COUNT(CASE WHEN is_late_delivery IS NOT NULL THEN 1 END) > 0 
        THEN (
            100.0 * COUNT(CASE WHEN is_late_delivery = TRUE THEN 1 END)
            / COUNT(CASE WHEN is_late_delivery IS NOT NULL THEN 1 END)
        )::FLOAT
        ELSE NULL 
    END AS late_delivery_rate_pct,
    AVG(total_delivery_days)::FLOAT AS avg_delivery_days,
    AVG(seller_dispatch_days)::FLOAT AS avg_seller_dispatch_days,
    AVG(carrier_transit_days)::FLOAT AS avg_carrier_transit_days,

    -- Sentiment
    AVG(review_score)::FLOAT AS avg_review_score,
    CASE 
        WHEN COUNT(CASE WHEN review_score IS NOT NULL THEN 1 END) > 0 
        THEN (
            100.0 * COUNT(CASE WHEN review_score <= 2 THEN 1 END)
            / COUNT(CASE WHEN review_score IS NOT NULL THEN 1 END)
        )::FLOAT
        ELSE NULL 
    END AS negative_review_rate_pct,

    -- Commercial
    COALESCE(SUM(freight_value), 0.00)::FLOAT AS freight_revenue,
    CASE 
        WHEN COALESCE(SUM(merchandise_revenue), 0.00) > 0 
        THEN (
            COALESCE(SUM(freight_value), 0.00) 
            / SUM(merchandise_revenue)
        )::FLOAT
        ELSE NULL 
    END AS freight_to_gmv_ratio
FROM period_orders;
"""


# ============================================================================
# 2. Dimensional Breakdown SQL Templates
# ============================================================================
BREAKDOWN_CUSTOMER_STATE_SQL = """
WITH current_period AS (
    SELECT
        COALESCE(customer_state, 'Unknown') AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(freight_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY COALESCE(customer_state, 'Unknown')
),
baseline_period AS (
    SELECT
        COALESCE(customer_state, 'Unknown') AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(freight_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY COALESCE(customer_state, 'Unknown')
)
SELECT
    COALESCE(c.slice_value, b.slice_value) AS slice_value,
    COALESCE(c.revenue, 0.00)::FLOAT AS current_revenue,
    COALESCE(b.revenue, 0.00)::FLOAT AS baseline_revenue,
    COALESCE(c.orders, 0)::FLOAT AS current_orders,
    COALESCE(b.orders, 0)::FLOAT AS baseline_orders,
    COALESCE(c.freight, 0.00)::FLOAT AS current_freight,
    COALESCE(b.freight, 0.00)::FLOAT AS baseline_freight
FROM current_period c
FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
"""

BREAKDOWN_ORDER_STATUS_SQL = """
WITH current_period AS (
    SELECT
        order_status AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(freight_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY order_status
),
baseline_period AS (
    SELECT
        order_status AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(freight_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY order_status
)
SELECT
    COALESCE(c.slice_value, b.slice_value) AS slice_value,
    COALESCE(c.revenue, 0.00)::FLOAT AS current_revenue,
    COALESCE(b.revenue, 0.00)::FLOAT AS baseline_revenue,
    COALESCE(c.orders, 0)::FLOAT AS current_orders,
    COALESCE(b.orders, 0)::FLOAT AS baseline_orders,
    COALESCE(c.freight, 0.00)::FLOAT AS current_freight,
    COALESCE(b.freight, 0.00)::FLOAT AS baseline_freight
FROM current_period c
FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
"""

BREAKDOWN_PAYMENT_TYPE_SQL = """
WITH current_period AS (
    SELECT
        COALESCE(primary_payment_type, 'unknown') AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(total_payment_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY COALESCE(primary_payment_type, 'unknown')
),
baseline_period AS (
    SELECT
        COALESCE(primary_payment_type, 'unknown') AS slice_value,
        SUM(merchandise_revenue) AS revenue,
        COUNT(order_id) AS orders,
        SUM(total_payment_value) AS freight
    FROM fact_order_analytics
    WHERE order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY COALESCE(primary_payment_type, 'unknown')
)
SELECT
    COALESCE(c.slice_value, b.slice_value) AS slice_value,
    COALESCE(c.revenue, 0.00)::FLOAT AS current_revenue,
    COALESCE(b.revenue, 0.00)::FLOAT AS baseline_revenue,
    COALESCE(c.orders, 0)::FLOAT AS current_orders,
    COALESCE(b.orders, 0)::FLOAT AS baseline_orders,
    COALESCE(c.freight, 0.00)::FLOAT AS current_freight,
    COALESCE(b.freight, 0.00)::FLOAT AS baseline_freight
FROM current_period c
FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
"""

BREAKDOWN_PRODUCT_CATEGORY_SQL = """
WITH current_period AS (
    SELECT
        product_category_name AS slice_value,
        SUM(total_gmv) AS revenue,
        SUM(orders_count) AS orders,
        SUM(total_freight_value) AS freight
    FROM fact_daily_kpis
    WHERE kpi_date >= %s::DATE AND kpi_date <= %s::DATE
    GROUP BY product_category_name
),
baseline_period AS (
    SELECT
        product_category_name AS slice_value,
        SUM(total_gmv) AS revenue,
        SUM(orders_count) AS orders,
        SUM(total_freight_value) AS freight
    FROM fact_daily_kpis
    WHERE kpi_date >= %s::DATE AND kpi_date <= %s::DATE
    GROUP BY product_category_name
)
SELECT
    COALESCE(c.slice_value, b.slice_value) AS slice_value,
    COALESCE(c.revenue, 0.00)::FLOAT AS current_revenue,
    COALESCE(b.revenue, 0.00)::FLOAT AS baseline_revenue,
    COALESCE(c.orders, 0)::FLOAT AS current_orders,
    COALESCE(b.orders, 0)::FLOAT AS baseline_orders,
    COALESCE(c.freight, 0.00)::FLOAT AS current_freight,
    COALESCE(b.freight, 0.00)::FLOAT AS baseline_freight
FROM current_period c
FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
"""

BREAKDOWN_SELLER_SQL = """
WITH current_period AS (
    SELECT
        oi.seller_id AS slice_value,
        SUM(oi.price) AS revenue,
        COUNT(DISTINCT oi.order_id) AS orders,
        SUM(oi.freight_value) AS freight
    FROM fact_order_analytics foa
    JOIN order_items oi ON foa.order_id = oi.order_id
    WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY oi.seller_id
),
baseline_period AS (
    SELECT
        oi.seller_id AS slice_value,
        SUM(oi.price) AS revenue,
        COUNT(DISTINCT oi.order_id) AS orders,
        SUM(oi.freight_value) AS freight
    FROM fact_order_analytics foa
    JOIN order_items oi ON foa.order_id = oi.order_id
    WHERE foa.order_purchase_timestamp >= %s::TIMESTAMPTZ
      AND foa.order_purchase_timestamp < (%s::DATE + INTERVAL '1 day')::TIMESTAMPTZ
    GROUP BY oi.seller_id
)
SELECT
    COALESCE(c.slice_value, b.slice_value) AS slice_value,
    COALESCE(c.revenue, 0.00)::FLOAT AS current_revenue,
    COALESCE(b.revenue, 0.00)::FLOAT AS baseline_revenue,
    COALESCE(c.orders, 0)::FLOAT AS current_orders,
    COALESCE(b.orders, 0)::FLOAT AS baseline_orders,
    COALESCE(c.freight, 0.00)::FLOAT AS current_freight,
    COALESCE(b.freight, 0.00)::FLOAT AS baseline_freight
FROM current_period c
FULL OUTER JOIN baseline_period b ON c.slice_value = b.slice_value;
"""
