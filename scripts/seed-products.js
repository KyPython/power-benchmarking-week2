#!/usr/bin/env node
/**
 * Seed Products Script
 * 
 * Run this to populate the products table in Supabase:
 *   node scripts/seed-products.js
 * 
 * Or with npx:
 *   npx tsx scripts/seed-products.js
 */

const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SECRET_KEY) must be set');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

const defaultProducts = [
  {
    polar_product_id: 'prod_free',
    name: 'Free',
    description: 'Basic power monitoring for personal use',
    plan: 'free',
    price_amount: 0,
    price_currency: 'usd',
    is_active: true,
  },
  {
    polar_product_id: 'prod_premium',
    name: 'Premium',
    description: 'Unlimited sessions with advanced analytics',
    plan: 'premium',
    price_amount: 999,
    price_currency: 'usd',
    is_active: true,
  },
  {
    polar_product_id: 'prod_enterprise',
    name: 'Enterprise',
    description: 'Team collaboration and custom integrations',
    plan: 'enterprise',
    price_amount: 4999,
    price_currency: 'usd',
    is_active: true,
  },
];

async function seedProducts() {
  console.log('Seeding products...\n');
  
  for (const product of defaultProducts) {
    // Check if product exists
    const { data: existing } = await supabase
      .from('products')
      .select('id')
      .eq('polar_product_id', product.polar_product_id)
      .single();
    
    if (existing) {
      // Update existing
      const { error } = await supabase
        .from('products')
        .update({
          name: product.name,
          description: product.description,
          plan: product.plan,
          price_amount: product.price_amount,
          price_currency: product.price_currency,
          is_active: product.is_active,
          updated_at: new Date().toISOString(),
        })
        .eq('polar_product_id', product.polar_product_id);
      
      if (error) {
        console.error(`❌ Failed to update ${product.name}:`, error.message);
      } else {
        console.log(`✓ Updated: ${product.name} (${product.plan})`);
      }
    } else {
      // Insert new
      const { error } = await supabase
        .from('products')
        .insert(product);
      
      if (error) {
        console.error(`❌ Failed to insert ${product.name}:`, error.message);
      } else {
        console.log(`✓ Inserted: ${product.name} (${product.plan})`);
      }
    }
  }
  
  // Verify
  const { data: products } = await supabase
    .from('products')
    .select('*')
    .eq('is_active', true)
    .order('price_amount');
  
  console.log('\n📋 Active Products:');
  for (const p of products || []) {
    const price = p.price_amount === 0 ? 'FREE' : `$${(p.price_amount / 100).toFixed(2)}`;
    console.log(`  • ${p.name}: ${price} (${p.plan})`);
  }
  
  console.log('\n✅ Seed complete!');
}

seedProducts().catch(console.error);
