/**
 * Activation Code API
 * 
 * GET /api/activation-code?email=user@example.com
 * Retrieve activation code for an email (if exists and not expired)
 * 
 * POST /api/activation-code
 * Resend activation code email
 */

import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get('email');
  
  if (!email) {
    return NextResponse.json(
      { error: 'Email is required' },
      { status: 400 }
    );
  }

  try {
    // Query device_codes table for this email
    const { data, error } = await supabase
      .from('device_codes')
      .select('*')
      .eq('email', email.toLowerCase())
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (error || !data) {
      return NextResponse.json(
        { error: 'No activation code found for this email' },
        { status: 404 }
      );
    }

    // Check if expired
    const expiresAt = new Date(data.expires_at).getTime();
    if (Date.now() > expiresAt) {
      return NextResponse.json(
        { error: 'Activation code has expired. Please contact support.' },
        { status: 410 }
      );
    }

    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app';
    
    return NextResponse.json({
      code: data.code,
      expiresAt: expiresAt,
      activationUrl: `${baseUrl}/activate?code=${data.code}`,
      status: data.status,
    });
  } catch (error) {
    console.error('[ActivationCode] Error:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve activation code' },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { email } = body;
    
    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    // Get existing code
    const { data: existingCode } = await supabase
      .from('device_codes')
      .select('*')
      .eq('email', email.toLowerCase())
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (!existingCode) {
      return NextResponse.json(
        { error: 'No activation code found. Please complete checkout first.' },
        { status: 404 }
      );
    }

    // Resend activation email
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app';
    const resendResponse = await fetch(`${baseUrl}/api/send-activation-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        code: existingCode.code,
        activationUrl: `${baseUrl}/activate?code=${existingCode.code}`,
        productName: 'Premium Tier'
      })
    });

    if (!resendResponse.ok) {
      return NextResponse.json(
        { error: 'Failed to resend email' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Activation email resent',
      code: existingCode.code,
    });
  } catch (error) {
    console.error('[ActivationCode] Error:', error);
    return NextResponse.json(
      { error: 'Failed to resend activation code' },
      { status: 500 }
    );
  }
}
