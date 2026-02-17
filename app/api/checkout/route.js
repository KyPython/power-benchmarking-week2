/**
 * Checkout API - Create Polar Checkout Session
 * 
 * Creates a checkout URL for Polar.sh products without using
 * the @polar-sh/nextjs package (which requires Next.js 15).
 */

import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const productId = searchParams.get('product_id') || process.env.POLAR_DEFAULT_PRODUCT_ID;
  const successUrl = searchParams.get('success_url') || process.env.POLAR_SUCCESS_URL || `${process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app'}/success`;
  const customerEmail = searchParams.get('email');

  if (!productId) {
    return NextResponse.json(
      { error: 'Product ID is required' },
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
    });
  } catch (error) {
    console.error('[Checkout] Error:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    );
  }
}
