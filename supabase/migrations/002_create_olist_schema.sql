-- ============================================================================
-- Migration 002: Olist Brazilian E-Commerce Relational Schema
-- ============================================================================
-- RootCause AI Analytical Database Foundation
--
-- ARCHITECTURAL NOTES & GRAIN DEFINITIONS:
-- 1. Normalization:
--    This schema is strictly normalized across 8 core relational entities.
--    Each table represents a clear domain grain:
--    - customers:          1 row per order customer transaction account
--    - sellers:            1 row per merchant / seller partner
--    - product_categories: 1 row per category translation
--    - products:           1 row per unique product SKU
--    - orders:             1 row per order transaction
--    - order_items:        1 row per individual line item inside an order
--    - payments:           1 row per payment installment / tender split
--    - reviews:            1 row per customer review survey entry
--
-- 2. CRITICAL REVENUE INTEGRITY RULE:
--    DO NOT directly join `order_items` and `payments` without pre-aggregation!
--    An order can have N items and M payment splits.
--    A direct join (orders JOIN order_items JOIN payments) produces an N x M
--    cartesian explosion that silently duplicates prices and payment values.
--    Always aggregate `order_items` at the `order_id` grain before joining
--    to `payments`, or vice versa.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Product Categories Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_categories (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

COMMENT ON TABLE product_categories IS 'Lookup table mapping Portuguese category names to English translations';

-- ----------------------------------------------------------------------------
-- 2. Customers Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE INDEX IF NOT EXISTS idx_customers_unique_id 
    ON customers(customer_unique_id);

COMMENT ON TABLE customers IS 'Customer transaction accounts (customer_id is per-order, customer_unique_id identifies the real buyer)';

-- ----------------------------------------------------------------------------
-- 3. Sellers Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

COMMENT ON TABLE sellers IS 'Marketplace sellers / merchants selling products on Olist';

-- ----------------------------------------------------------------------------
-- 4. Products Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT REFERENCES product_categories(product_category_name) ON DELETE SET NULL,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER
);

CREATE INDEX IF NOT EXISTS idx_products_category 
    ON products(product_category_name);

COMMENT ON TABLE products IS 'Product catalog master containing physical dimensions and category linkages';

-- ----------------------------------------------------------------------------
-- 5. Orders Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id 
    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status 
    ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp 
    ON orders(order_purchase_timestamp);

COMMENT ON TABLE orders IS 'Order header grain (1 row per order placed on the platform)';

-- ----------------------------------------------------------------------------
-- 6. Order Items Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    order_item_id INTEGER NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    seller_id TEXT NOT NULL REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMPTZ NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    freight_value NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_product_id 
    ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller_id 
    ON order_items(seller_id);

COMMENT ON TABLE order_items IS 'Line item grain (1 row per item inside an order; primary source of price and freight metrics)';

-- ----------------------------------------------------------------------------
-- 7. Payments Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    payment_sequential INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments INTEGER NOT NULL DEFAULT 1,
    payment_value NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE INDEX IF NOT EXISTS idx_payments_order_id 
    ON payments(order_id);

COMMENT ON TABLE payments IS 'Payment transaction grain (1 row per payment tender/method used to settle an order)';

-- ----------------------------------------------------------------------------
-- 8. Reviews Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    review_score INTEGER NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMPTZ NOT NULL,
    review_answer_timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (review_id, order_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_order_id 
    ON reviews(order_id);

COMMENT ON TABLE reviews IS 'Customer satisfaction review surveys linked to orders';
