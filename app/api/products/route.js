/**
 * Products API - Fetch available products from database
 * 
 * Returns all active products from the products table
 */

import { NextResponse } from 'next/server';
import { getAllProducts, getProductByPlan } from '@/lib/supabase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const plan = searchParams.get('plan');
    
    // Get specific plan
    if (plan) {
      const product = await getProductByPlan(plan);
      
      if (!product) {
        return NextResponse.json(
          { error: `Product not found for plan: ${plan}` },
          { status: 404 }
        );
      }
      
      return NextResponse.json(product);
    }
    
    // Get all products
    const products = await getAllProducts();
    
    return NextResponse.json({
      products,
      count: products.length
    });
  } catch (error) {
    console.error('[Products] Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch products' },
      { status: 500 }
    );
  }
}
