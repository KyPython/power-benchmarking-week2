/**
 * Device Activation API
 *
 * POST /api/device-codes
 * Create a new device activation code.
 *
 * NOTE: In-memory storage is shared via the exported `deviceCodes`
 * map from the Polar webhook route so that:
 * - Webhooks can create codes
 * - /api/device-codes and /api/activate can read/update them
 *
 * In production, replace this with a shared store (Redis/DB).
 */

import { NextResponse } from 'next/server';
import { randomBytes } from 'crypto';
import { deviceCodes } from '../webhooks/polar/route';

// Configuration
const CODE_EXPIRY_MS = 15 * 60 * 1000; // 15 minutes to activate

function generateActivationCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 8; i++) {
    if (i === 4) code += '-';
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

function generateLicenseToken() {
  return 'pbs_' + randomBytes(32).toString('hex');
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { email, plan = 'premium', checkoutId } = body;

    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 },
      );
    }

    const code = generateActivationCode();
    const token = generateLicenseToken();
    const expiresAt = Date.now() + CODE_EXPIRY_MS;

    deviceCodes.set(code.toUpperCase(), {
      email,
      plan,
      expiresAt,
      activated: false,
      activatedAt: null,
      token,
      checkoutId,
    });

    console.log(
      `[DeviceCodes] Created code ${code} for ${email}, plan: ${plan}`,
    );

    const baseUrl =
      process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';

    return NextResponse.json({
      code,
      expiresAt,
      verificationUrl: `${baseUrl}/activate?code=${code}`,
      instructions:
        'Visit the verification URL and click to confirm activation',
    });
  } catch (error) {
    console.error('[DeviceCodes] Error creating code:', error);
    return NextResponse.json(
      { error: 'Failed to create activation code' },
      { status: 500 },
    );
  }
}
