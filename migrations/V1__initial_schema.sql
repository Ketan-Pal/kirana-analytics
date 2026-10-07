-- V1__initial_schema.sql
-- Flyway DDL Migration: Core Tables, Constraints, and Indexes

-- 1. Schema Version Table (Audit log for all migrations)
CREATE TABLE IF NOT EXISTS schema_version (
    installed_rank SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'SQL',
    script VARCHAR(1000) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    installed_by VARCHAR(100) NOT NULL,
    installed_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL
);

-- 2. Master Product Catalog Table
CREATE TABLE IF NOT EXISTS catalog_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    standard_unit VARCHAR(50) NOT NULL DEFAULT 'packet',
    default_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (default_price >= 0),
    seasonality_tag VARCHAR(50) DEFAULT 'All-Season',
    aliases JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Sales Batches Table (One batch per daily notepad submission)
CREATE TABLE IF NOT EXISTS sales_batches (
    id SERIAL PRIMARY KEY,
    batch_date DATE NOT NULL,
    weather VARCHAR(50) DEFAULT 'Normal',
    festival VARCHAR(100) DEFAULT 'None',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_json JSONB,
    items_count INTEGER DEFAULT 0 CHECK (items_count >= 0),
    total_revenue NUMERIC(12, 2) DEFAULT 0.00 CHECK (total_revenue >= 0)
);

-- 4. Transaction Line Items Table
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES sales_batches(id) ON DELETE CASCADE,
    sale_no INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    sale_time VARCHAR(20) DEFAULT '',
    time_period VARCHAR(20) NOT NULL CHECK (time_period IN ('Morning', 'Afternoon', 'Evening', 'Night')),
    month_str VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    day_of_week VARCHAR(15) NOT NULL,
    weather VARCHAR(50) DEFAULT 'Normal',
    festival VARCHAR(100) DEFAULT 'None',
    basket_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (quantity > 0),
    unit VARCHAR(50) NOT NULL DEFAULT 'packet',
    pack_size VARCHAR(50) DEFAULT 'Standard',
    unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (unit_price >= 0),
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_sale_items_date ON sale_items(sale_date);
CREATE INDEX IF NOT EXISTS idx_sale_items_month ON sale_items(month_str);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_name);
CREATE INDEX IF NOT EXISTS idx_sale_items_basket ON sale_items(basket_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_weather ON sale_items(weather);
CREATE INDEX IF NOT EXISTS idx_sale_items_festival ON sale_items(festival);
CREATE INDEX IF NOT EXISTS idx_sale_items_date_prod ON sale_items(sale_date, product_name);
