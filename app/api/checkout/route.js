/**
 * Checkout API - Create Polar Checkout Session
 * 
 * Creates a checkout URL for Polar.sh products.
 * Uses products from database if available, falls back to environment variables.
 */

import { NextResponse } from 'next/server';
import { getProductByPlan, getAllProducts } from '@/lib/supabase';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const plan = searchParams.get('plan') || 'premium';
  const successUrl = searchParams.get('success_url') || process.env.POLAR_SUCCESS_URL || `${process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app'}/success`;
  const customerEmail = searchParams.get('email');

  // Try to get product from database
  let productId = process.env.POLAR_DEFAULT_PRODUCT_ID;
  
  try {
    const product = await getProductByPlan(plan);
    if (product) {
      productId = product.polar_product_id;
    }
  } catch (e) {
    console.log('[Checkout] Database not available, using env var');
  }

  if (!productId) {
    return NextResponse.json(
      { error: `No product configured for plan: ${plan}` },
      { status: 400 }
    );
  }

  try {
    const polarToken = process.env.POLAR_ACCESS_TOKEN;
    
    if (!polarToken) {
      // Return a placeholder URL for development
      return NextResponse.json({
        checkoutUrl: `https://polar.sh/${productId}?success_url=${encodeURIComponent(successUrl)}`,
        message: 'Development mode - set POLAR_ACCESS_TOKEN for production',
        plan,
      });
    }

    // Create checkout using Polar API
    const response = await fetch('https://api.polar.sh/v1/checkouts', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${polarToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id: productId,
        success_url: successUrl,
        customer_email: customerEmail,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('[Checkout] Polar API error:', error);
      return NextResponse.json(
        { error: 'Failed to create checkout' },
        { status: 500 }
      );
    }

    const data = await response.json();
    
    return NextResponse.json({
      checkoutUrl: data.url,
      plan,
    });
  } catch (error) {
    console.error('[Checkout] Error:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    );
  }
}

// Also return available plans
export async function POST(request) {
  try {
    const products = await getAllProducts();
    
    if (products.length > 0) {
      return NextResponse.json({
        plans: products.map(p => ({
          plan: p.slug,
          name: p.name,
          price: p.price_cents,
          currency: 'usd',
        }))
      });
    }
    
    // Fallback to environment variables
    return NextResponse.json({
      plans: [
        { plan: 'free', name: 'Free', price: 0, currency: 'usd' },
        { plan: 'premium', name: 'Premium', price: process.env.POLAR_PREMIUM_PRICE || 999, currency: 'usd' },
        { plan: 'enterprise', name: 'Enterprise', price: process.env.POLAR_ENTERPRISE_PRICE || 4999, currency: 'usd' },
      ]
    });
  } catch (e) {
    return NextResponse.json({
      plans: [
        { plan: 'free', name: 'Free', price: 0, currency: 'usd' },
        { plan: 'premium', name: 'Premium', price: 999, currency: 'usd' },
        { plan: 'enterprise', name: 'Enterprise', price: 4999, currency: 'usd' },
      ]
    });
  }
}
