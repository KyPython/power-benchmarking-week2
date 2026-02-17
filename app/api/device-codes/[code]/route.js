import { NextResponse } from 'next/server';
import { getDeviceCode } from '../../../../lib/supabase';

const TOKEN_EXPIRY_DAYS = 30;

export async function GET(request, { params }) {
  const { code } = params || {};

  if (!code) {
    return NextResponse.json(
      { error: 'Code is required' },
      { status: 400 },
    );
  }

  const normalizedCode = String(code).toUpperCase();
  
  // Get from Supabase
  const deviceData = await getDeviceCode(normalizedCode);

  if (!deviceData) {
    return NextResponse.json(
      { error: 'Invalid or expired code' },
      { status: 404 },
    );
  }

  const expiresAt = new Date(deviceData.expires_at).getTime();
  if (Date.now() > expiresAt) {
    return NextResponse.json(
      { error: 'Code has expired' },
      { status: 410 },
    );
  }

  return NextResponse.json({
    code: normalizedCode,
    activated: deviceData.status === 'completed',
    expiresAt: expiresAt,
    ...(deviceData.status === 'completed' && deviceData.token
      ? {
          token: deviceData.token,
          tokenExpiresAt:
            Date.now() + TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000,
        }
      : {}),
  });
}
