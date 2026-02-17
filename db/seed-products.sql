-- Seed products for Power Benchmarking Suite
-- Run this after applying schema.sql to populate products

-- Insert default products (these will be overwritten when syncing from Polar)
INSERT INTO products (polar_product_id, name, description, plan, price_amount, price_currency, is_active) VALUES
('prod_free', 'Free', 'Basic power monitoring for personal use', 'free', 0, 'usd', true),
('prod_premium', 'Premium', 'Unlimited sessions with advanced analytics', 'premium', 999, 'usd', true),
('prod_enterprise', 'Enterprise', 'Team collaboration and custom integrations', 'enterprise', 4999, 'usd', true)
ON CONFLICT (polar_product_id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  plan = EXCLUDED.plan,
  price_amount = EXCLUDED.price_amount,
  is_active = true,
  updated_at = CURRENT_TIMESTAMP;
