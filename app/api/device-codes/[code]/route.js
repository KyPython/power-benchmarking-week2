import { NextResponse } from 'next/server';
import { deviceCodes } from '../../webhooks/polar/route';

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
  const deviceData = deviceCodes.get(normalizedCode);

  if (!deviceData) {
    return NextResponse.json(
      { error: 'Invalid or expired code' },
      { status: 404 },
    );
  }

  if (Date.now() > deviceData.expiresAt) {
    deviceCodes.delete(normalizedCode);
    return NextResponse.json(
      { error: 'Code has expired' },
      { status: 410 },
    );
  }

  return NextResponse.json({
    code: normalizedCode,
    activated: deviceData.activated,
    expiresAt: deviceData.expiresAt,
    ...(deviceData.activated && deviceData.token
      ? {
          token: deviceData.token,
          tokenExpiresAt:
            Date.now() + TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000,
        }
      : {}),
  });
}

