/**
 * Entitlement API - Check user's premium status
 * 
 * GET /api/entitlement?email=user@example.com
 */

import { NextRequest, NextResponse } from 'next/server';
import { getUserByEmail, getEntitlement, getDevices } from '@/lib/supabase';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get('email');
    const token = searchParams.get('token');

    if (!email) {
      return NextResponse.json(
        { error: 'Email required' },
        { status: 400 }
      );
    }

    // Get user
    const user = await getUserByEmail(email);
    
    if (!user) {
      return NextResponse.json({
        tier: 'free',
        user: null
      });
    }

    // Get entitlement
    const entitlement = await getEntitlement(user.id);
    const devices = await getDevices(user.id);

    return NextResponse.json({
      tier: entitlement?.tier || 'free',
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
      devices,
      subscription: entitlement ? {
        tier: entitlement.tier,
        subscriptionId: entitlement.subscription_id,
        expiresAt: entitlement.expires_at,
      } : null
    });
  } catch (error) {
    console.error('[Entitlement] Error:', error);
    return NextResponse.json(
      { error: 'Failed to check entitlement' },
      { status: 500 }
    );
  }
}
