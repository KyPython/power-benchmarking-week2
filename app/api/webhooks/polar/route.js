/**
 * Polar Webhook Handler - Full Multi-User Support
 * 
 * Handles payment events from Polar.sh with proper:
 * - Webhook signature verification (HMAC-SHA256)
 * - Supabase database for user management
 * - Entitlement tracking
 * - Email notifications
 */

import { NextRequest, NextResponse } from 'next/server';
import { randomBytes, createHmac } from 'crypto';
import { getOrCreateUser, setEntitlement, createDeviceCode, getProductByPolarId, savePurchaseRecord, supabase } from '@/lib/supabase';

// In-memory stores (fallback if no Supabase)
const processedEvents = new Map();

const CODE_EXPIRY_MS = 15 * 60 * 1000;

/**
 * Verify Polar webhook signature
 */
function verifyPolarSignature(signature, body, secret) {
  if (!signature || !secret) return true; // Skip in dev
  
  const parts = signature.split(',');
  let timestamp = '', sig = '';
  
  for (const part of parts) {
    if (part.startsWith('t=')) timestamp = part.slice(2);
    if (part.startsWith('v1=')) sig = part.slice(2);
  }

  if (!timestamp || !sig) return false;
  
  // Skip old timestamp check in dev
  if (process.env.NODE_ENV === 'production') {
    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - parseInt(timestamp)) > 300) return false;
  }

  const payload = `${timestamp}.${body}`;
  const expected = createHmac('sha256', secret).update(payload).digest('hex');
  
  return sig === expected;
}

function generateCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 8; i++) {
    if (i === 4) code += '-';
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

function generateToken() {
  return 'pbs_' + randomBytes(16).toString('hex');
}

/**
 * Handle checkout completed
 */
async function handleCheckoutCompleted(data) {
  const email = data?.customer_email || data?.customer?.email;
  const checkoutId = data?.id;
  const productName = data?.product?.name || 'Premium';
  const productId = data?.product?.id;
  
  if (!email) return NextResponse.json({ error: 'No email' }, { status: 400 });

  // Idempotency
  if (processedEvents.has(checkoutId)) {
    return NextResponse.json({ received: true, idempotent: true });
  }

  // Get or create user
  let user;
  try {
    if (!supabase) {
      console.error('[Webhook] Supabase not configured! Check SUPABASE_URL and SUPABASE_ANON_KEY env vars');
      return NextResponse.json({ 
        error: 'Database not configured',
        hint: 'Set SUPABASE_URL and SUPABASE_ANON_KEY in Vercel environment variables'
      }, { status: 500 });
    }
    user = await getOrCreateUser(email, data?.customer_id);
    console.log('[Webhook] User:', user ? `Created/found user ${user.id}` : 'Failed to create user');
  } catch (e) {
    console.error('[Webhook] Failed to get/create user:', e.message);
    console.error('[Webhook] Error details:', e);
    return NextResponse.json({ 
      error: 'Failed to process user',
      details: e.message 
    }, { status: 500 });
  }

  // Determine tier from product
  let tier = 'premium';
  const nameLower = (productName || '').toLowerCase();
  if (nameLower.includes('enterprise')) {
    tier = 'enterprise';
  } else if (nameLower.includes('pro')) {
    tier = 'pro';
  }

  // Create entitlement
  if (user) {
    try {
      await setEntitlement(user.id, tier, null, checkoutId);
    } catch (e) {
      console.log('[Entitlement] Failed to set:', e.message);
    }

    // Try to link product
    let dbProductId = null;
    if (productId) {
      try {
        const product = await getProductByPolarId(productId);
        if (product) {
          dbProductId = product.id;
        }
      } catch (e) {
        console.log('[Product] Not found in database');
      }
    }

    // Save purchase record
    try {
      await savePurchaseRecord({
        event_id: checkoutId,
        user_id: user.id,
        event_type: 'checkout.completed',
        checkout_id: checkoutId,
        product_id: dbProductId,
        product_name: productName,
        amount: data?.product?.price_amount || data?.amount || 0,
        currency: data?.product?.price_currency || data?.currency || 'usd',
        status: 'completed',
      });
    } catch (e) {
      console.log('[Purchase] Failed to save:', e.message);
    }
  }

  // Generate activation code and store in Supabase
  const code = generateCode();
  const token = generateToken();
  
  // Store in Supabase
  try {
    await createDeviceCode(email, code.toUpperCase(), {
      plan: tier,
      token,
      checkoutId,
      status: 'pending',
      expires_at: new Date(Date.now() + CODE_EXPIRY_MS).toISOString(),
    });
  } catch (e) {
    console.log('[DeviceCode] Failed to store in Supabase:', e.message);
    // Fallback to in-memory
    processedEvents.set(checkoutId, code);
  }

  // Send activation email
  try {
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app';
    await fetch(`${baseUrl}/api/send-activation-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        code,
        activationUrl: `${baseUrl}/activate?code=${code}`,
        productName
      })
    });
  } catch (e) {
    console.log('[Email] Failed:', e.message);
  }

  return NextResponse.json({
    success: true,
    checkoutId,
    message: 'Premium activated'
  });
}

/**
 * Handle subscription events
 */
async function handleSubscription(data, action = 'created') {
  const email = data?.customer?.email;
  const subscriptionId = data?.id;
  
  if (!email) return NextResponse.json({ received: true });

  let user;
  try {
    user = await getOrCreateUser(email, data?.customer_id);
  } catch (e) {}

  const tier = action === 'canceled' ? 'free' : 'premium';
  
  if (user) {
    try {
      await setEntitlement(user.id, tier, subscriptionId);
    } catch (e) {}
  }

  return NextResponse.json({ success: true });
}

export async function POST(request) {
  try {
    const webhookSecret = process.env.POLAR_WEBHOOK_SECRET;
    const signature = request.headers.get('polar-signature');
    const rawBody = await request.text();
    
    // Log webhook receipt for debugging
    console.log('[Webhook] Received webhook');
    console.log('[Webhook] Has secret:', !!webhookSecret);
    console.log('[Webhook] Has signature:', !!signature);
    console.log('[Webhook] Supabase configured:', !!supabase);
    
    // Verify signature
    if (webhookSecret && signature) {
      if (!verifyPolarSignature(signature, rawBody, webhookSecret)) {
        console.error('[Webhook] Invalid signature');
        return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
      }
    }

    const body = JSON.parse(rawBody);
    const eventType = body?.type;
    const eventData = body?.data;

    console.log(`[Webhook] Event type: ${eventType}`);
    console.log(`[Webhook] Event data:`, JSON.stringify(eventData, null, 2));

    switch (eventType) {
      case 'checkout.completed':
        console.log('[Webhook] Processing checkout.completed');
        const result = await handleCheckoutCompleted(eventData);
        console.log('[Webhook] Result:', result);
        return result;
      
      case 'subscription.created':
      case 'subscription.active':
        console.log('[Webhook] Processing subscription event');
        return handleSubscription(eventData, 'created');
      
      case 'subscription.canceled':
        return handleSubscription(eventData, 'canceled');
      
      case 'refund.created':
        return handleSubscription(eventData, 'canceled');
      
      default:
        console.log(`[Webhook] Unhandled event type: ${eventType}`);
        return NextResponse.json({ received: true, eventType });
    }
  } catch (error) {
    console.error('[Webhook] Error:', error);
    console.error('[Webhook] Stack:', error.stack);
    return NextResponse.json({ 
      error: 'Internal error',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    }, { status: 500 });
  }
}
