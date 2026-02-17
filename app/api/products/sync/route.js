/**
 * Products Sync API - Sync products from Polar to database
 * 
 * Fetches products from Polar API and stores them in the database.
 * Should be called during deployment or manually to update product catalog.
 */

import { NextResponse } from 'next/server';
import { createOrUpdateProduct, getAllProducts } from '@/lib/supabase';

export async function POST(request) {
  try {
    const polarToken = process.env.POLAR_ACCESS_TOKEN;
    
    if (!polarToken) {
      return NextResponse.json(
        { error: 'POLAR_ACCESS_TOKEN not configured' },
        { status: 500 }
      );
    }
    
    // Fetch products from Polar API
    const response = await fetch('https://api.polar.sh/v1/products', {
      headers: {
        'Authorization': `Bearer ${polarToken}`,
      },
    });
    
    if (!response.ok) {
      const error = await response.text();
      console.error('[Products Sync] Polar API error:', error);
      return NextResponse.json(
        { error: 'Failed to fetch products from Polar' },
        { status: 500 }
      );
    }
    
    const data = await response.json();
    const polarProducts = data.items || [];
    
    const results = [];
    
    for (const product of polarProducts) {
      // Determine slug based on product name/type
      let slug = 'free';
      const nameLower = (product.name || '').toLowerCase();
      
      if (nameLower.includes('enterprise')) {
        slug = 'enterprise';
      } else if (nameLower.includes('premium')) {
        slug = 'premium';
      } else if (nameLower.includes('pro')) {
        slug = 'pro';
      }
      
      const productData = {
        polar_product_id: product.id,
        name: product.name,
        slug,
        price_cents: product.prices?.[0]?.unit_amount || 0,
        interval: product.prices?.[0]?.recurring ? 'month' : 'one-time',
        active: !product.archived,
      };
      
      const saved = await createOrUpdateProduct(productData);
      results.push(saved);
    }
    
    return NextResponse.json({
      success: true,
      synced: results.length,
      products: results
    });
  } catch (error) {
    console.error('[Products Sync] Error:', error);
    return NextResponse.json(
      { error: 'Failed to sync products' },
      { status: 500 }
    );
  }
}

// Also allow GET for manual trigger in development
export async function GET() {
  return POST(new Request('http://localhost:3000/api/products/sync', {
    method: 'POST',
    body: JSON.stringify({})
  }));
}
