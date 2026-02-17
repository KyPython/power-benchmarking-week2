// Supabase client for database operations

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase = supabaseUrl && supabaseKey 
  ? createClient(supabaseUrl, supabaseKey)
  : null;

// Helper functions
export async function getUserByEmail(email) {
  if (!supabase) return null;
  const { data } = await supabase
    .from('users')
    .select('*')
    .eq('email', email)
    .single();
  return data;
}

export async function getOrCreateUser(email, polarCustomerId = null) {
  if (!supabase) return null;
  
  let user = await getUserByEmail(email);
  
  if (!user) {
    const { data, error } = await supabase
      .from('users')
      .insert({ email, polar_customer_id: polarCustomerId })
      .select()
      .single();
    
    if (error) throw error;
    user = data;
  }
  
  return user;
}

export async function getEntitlement(userId) {
  if (!supabase) return { tier: 'free' };
  
  const { data } = await supabase
    .from('entitlements')
    .select('*')
    .eq('user_id', userId)
    .eq('is_active', true)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();
  
  return data || { tier: 'free' };
}

export async function setEntitlement(userId, tier, subscriptionId = null, checkoutId = null) {
  if (!supabase) return null;
  
  // Deactivate old entitlements
  await supabase
    .from('entitlements')
    .update({ is_active: false })
    .eq('user_id', userId);
  
  // Insert new entitlement
  const { data, error } = await supabase
    .from('entitlements')
    .insert({
      user_id: userId,
      tier,
      subscription_id: subscriptionId,
      checkout_id: checkoutId,
      is_active: true,
    })
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function saveRun(userId, runData) {
  if (!supabase) return null;
  
  const { data, error } = await supabase
    .from('runs')
    .insert({
      user_id: userId,
      ...runData,
    })
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function getRuns(userId, limit = 50) {
  if (!supabase) return [];
  
  const { data } = await supabase
    .from('runs')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);
  
  return data || [];
}

export async function getDevices(userId) {
  if (!supabase) return [];
  
  const { data } = await supabase
    .from('devices')
    .select('*')
    .eq('user_id', userId)
    .order('last_seen_at', { ascending: false });
  
  return data || [];
}

export async function registerDevice(userId, deviceName, platform) {
  if (!supabase) return null;
  
  const { data: existing } = await supabase
    .from('devices')
    .select('id')
    .eq('user_id', userId)
    .eq('device_name', deviceName)
    .single();
  
  if (existing) {
    const { data } = await supabase
      .from('devices')
      .update({ last_seen_at: new Date().toISOString() })
      .eq('id', existing.id)
      .select()
      .single();
    return data;
  }
  
  const { data, error } = await supabase
    .from('devices')
    .insert({
      user_id: userId,
      device_name: deviceName,
      platform,
    })
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

// Device code functions for OAuth-like device flow
export async function createDeviceCode(email, code, extra = {}) {
  if (!supabase) return null;
  
  const { data, error } = await supabase
    .from('device_codes')
    .insert({
      code,
      email,
      status: extra.status || 'pending',
      expires_at: extra.expires_at || new Date(Date.now() + 10 * 60 * 1000).toISOString(),
      plan: extra.plan || 'free',
      token: extra.token || null,
      checkout_id: extra.checkoutId || null,
    })
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function getDeviceCode(code) {
  if (!supabase) return null;
  
  const { data } = await supabase
    .from('device_codes')
    .select('*')
    .eq('code', code)
    .single();
  
  return data;
}

export async function updateDeviceCode(code, updates) {
  if (!supabase) return null;
  
  const { data, error } = await supabase
    .from('device_codes')
    .update(updates)
    .eq('code', code)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

// Product functions
export async function getProductByPolarId(polarProductId) {
  if (!supabase) return null;
  
  const { data } = await supabase
    .from('products')
    .select('*')
    .eq('polar_product_id', polarProductId)
    .eq('active', true)
    .single();
  
  return data;
}

export async function getProductByPlan(slug) {
  if (!supabase) return null;
  
  const { data } = await supabase
    .from('products')
    .select('*')
    .eq('slug', slug)
    .eq('active', true)
    .single();
  
  return data;
}

export async function getAllProducts() {
  if (!supabase) return [];
  
  const { data } = await supabase
    .from('products')
    .select('*')
    .eq('active', true)
    .order('price_cents', { ascending: true });
  
  return data || [];
}

export async function createOrUpdateProduct(product) {
  if (!supabase) return null;
  
  const { data: existing } = await supabase
    .from('products')
    .select('id')
    .eq('polar_product_id', product.polar_product_id)
    .single();
  
  if (existing) {
    const { data, error } = await supabase
      .from('products')
      .update({
        name: product.name,
        slug: product.slug,
        price_cents: product.price_cents,
        interval: product.interval,
        active: product.active ?? true,
        updated_at: new Date().toISOString(),
      })
      .eq('polar_product_id', product.polar_product_id)
      .select()
      .single();
    
    if (error) throw error;
    return data;
  }
  
  const { data, error } = await supabase
    .from('products')
    .insert(product)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function savePurchaseRecord(record) {
  if (!supabase) return null;
  
  const { data, error } = await supabase
    .from('purchase_records')
    .insert(record)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}
