/**
 * Device Activation Confirmation API
 *
 * POST /api/activate - Confirm device activation from web UI
 *
 * Uses Supabase for storage so codes created by webhooks or
 * /api/device-codes can be activated here.
 */

import { NextResponse } from 'next/server';
import { getDeviceCode, updateDeviceCode, getUserByEmail } from '../../../lib/supabase';

export async function POST(request) {
  try {
    const body = await request.json();
    const { code, confirm = true } = body;

    if (!code) {
      return NextResponse.json(
        { error: 'Code is required' },
        { status: 400 }
      );
    }

    const normalizedCode = String(code).toUpperCase();
    
    // Get from Supabase
    const deviceData = await getDeviceCode(normalizedCode);

    if (!deviceData) {
      return NextResponse.json(
        { error: 'Invalid code' },
        { status: 404 }
      );
    }

    // Check if already activated
    if (deviceData.status === 'completed') {
      return NextResponse.json({
        success: true,
        message: 'Already activated',
        token: deviceData.token
      });
    }

    // Check if expired
    const expiresAt = new Date(deviceData.expires_at).getTime();
    if (Date.now() > expiresAt) {
      return NextResponse.json(
        { error: 'Code has expired' },
        { status: 410 }
      );
    }

    // Activate the device
    if (confirm) {
      await updateDeviceCode(normalizedCode, {
        status: 'completed',
        activated_at: new Date().toISOString(),
      });
      
      console.log(`[Activate] Device ${normalizedCode} activated for ${deviceData.email}`);
    }

    return NextResponse.json({
      success: true,
      message: 'Device activated successfully',
      email: deviceData.email,
      plan: deviceData.plan
    });
  } catch (error) {
    console.error('[Activate] Error:', error);
    return NextResponse.json(
      { error: 'Failed to activate device' },
      { status: 500 }
    );
  }
}
