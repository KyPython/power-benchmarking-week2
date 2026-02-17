-- Power Benchmarking Suite - Complete Database Schema
-- Multi-user, cloud sync, team collaboration support

-- ============================================
-- USERS
-- ============================================
-- Core user table (keyed by Polar customer ID)

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    polar_customer_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_polar_id ON users(polar_customer_id);

-- ============================================
-- ENTITLEMENTS  
-- ============================================
-- Centralized tier management

CREATE TABLE IF NOT EXISTS entitlements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    subscription_id VARCHAR(255),
    checkout_id VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entitlements_user ON entitlements(user_id);
CREATE INDEX IF NOT EXISTS idx_entitlements_active ON entitlements(user_id, is_active);

-- ============================================
-- RUNS / BENCHMARK RESULTS
-- ============================================
-- Cloud-synced benchmark runs

CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255),
    command VARCHAR(100),
    duration_seconds INTEGER,
    avg_power_watts DECIMAL(10,2),
    peak_power_watts DECIMAL(10,2),
    cpu_samples INTEGER,
    gpu_samples INTEGER,
    device_count INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(user_id, project_name);

-- ============================================
-- DEVICES
-- ============================================
-- User's registered devices for sync

CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,
    platform VARCHAR(50),
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);

-- ============================================
-- ACTIVATION CODES
-- ============================================
-- Legacy - can be replaced by entitlements

CREATE TABLE IF NOT EXISTS activation_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'premium',
    checkout_id VARCHAR(255),
    activated BOOLEAN DEFAULT FALSE,
    activated_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activation_codes_code ON activation_codes(code);

-- ============================================
-- DEVICE CODES (OAuth-like flow)
-- ============================================

CREATE TABLE IF NOT EXISTS device_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    plan VARCHAR(50) DEFAULT 'free',
    token VARCHAR(255),
    checkout_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    activated_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_codes_code ON device_codes(code);
CREATE INDEX IF NOT EXISTS idx_device_codes_email ON device_codes(email);

-- ============================================
-- PRODUCTS
-- ============================================
-- Product catalog synced from Polar

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    polar_product_id VARCHAR(255) UNIQUE NOT NULL,
    price_cents INTEGER DEFAULT 0,
    interval VARCHAR(20) DEFAULT 'month',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_polar_id ON products(polar_product_id);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);

-- ============================================
-- PURCHASE RECORDS (Audit)
-- ============================================

CREATE TABLE IF NOT EXISTS purchase_records (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    checkout_id VARCHAR(255),
    subscription_id VARCHAR(255),
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(255),
    amount INTEGER,
    currency VARCHAR(10),
    status VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- USAGE LOGS
-- ============================================

CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    command VARCHAR(100),
    duration_seconds INTEGER,
    device_count INTEGER,
    tier VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- API KEYS
-- ============================================

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- ============================================
-- WEBHOOK DELIVERIES
-- ============================================

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255),
    status VARCHAR(20),
    response_code INTEGER,
    error_message TEXT,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
