/**
 * Device Activation API
 *
 * POST /api/device-codes
 * Create a new device activation code.
 *
 * Uses Supabase for storage to support multiple server instances
 * and persistence across restarts.
 */

import { NextResponse } from 'next/server';
import { randomBytes } from 'crypto';
import { createDeviceCode } from '../../../lib/supabase';

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
    const expiresAt = new Date(Date.now() + CODE_EXPIRY_MS).toISOString();

    // Store in Supabase
    await createDeviceCode(email, code.toUpperCase(), {
      plan,
      token,
      checkoutId,
      status: 'pending',
      expires_at: expiresAt,
    });

    console.log(
      `[DeviceCodes] Created code ${code} for ${email}, plan: ${plan}`,
    );

    const baseUrl =
      process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';

    return NextResponse.json({
      code,
      expiresAt: Date.now() + CODE_EXPIRY_MS,
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
