/**
 * Device Activation Confirmation API
 *
 * POST /api/activate - Confirm device activation from web UI
 *
 * Uses the shared in-memory `deviceCodes` map exported from the
 * Polar webhook route so that codes created by webhooks or
 * /api/device-codes can be activated here.
 */

import { NextResponse } from 'next/server';
import { deviceCodes } from '../webhooks/polar/route';

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
    const deviceData = deviceCodes.get(normalizedCode);

    if (!deviceData) {
      return NextResponse.json(
        { error: 'Invalid code' },
        { status: 404 }
      );
    }

    // Check if already activated
    if (deviceData.activated) {
      return NextResponse.json({
        success: true,
        message: 'Already activated',
        token: deviceData.token
      });
    }

    // Activate the device
    if (confirm) {
      deviceData.activated = true;
      deviceData.activatedAt = Date.now();
      
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
