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

    if (error) {
      console.error('[ActivationCode] Database error:', error);
      return NextResponse.json(
        { error: `Database error: ${error.message}` },
        { status: 500 }
      );
    }

    if (!data) {
      return NextResponse.json(
        { 
          error: 'No activation code found for this email',
          hint: 'This usually means the checkout webhook hasn\'t been processed yet. Please wait a few minutes and try again.'
        },
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

    if (!supabase) {
      console.error('[ActivationCode] Supabase not configured');
      return NextResponse.json(
        { error: 'Database not configured. Please check your Supabase settings.' },
        { status: 500 }
      );
    }

    // Get existing code
    const { data: existingCode, error: dbError } = await supabase
      .from('device_codes')
      .select('*')
      .eq('email', email.toLowerCase())
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (dbError) {
      console.error('[ActivationCode] Database error:', dbError);
      return NextResponse.json(
        { error: `Database error: ${dbError.message}` },
        { status: 500 }
      );
    }

    if (!existingCode) {
      return NextResponse.json(
        { 
          error: 'No activation code found for this email.',
          hint: 'This usually means the checkout webhook hasn\'t been processed yet. Please wait a few minutes and try again, or contact support.'
        },
        { status: 404 }
      );
    }

    // Check if expired
    const expiresAt = new Date(existingCode.expires_at).getTime();
    if (Date.now() > expiresAt) {
      return NextResponse.json(
        { 
          error: 'Activation code has expired.',
          hint: 'Please contact support to get a new activation code.'
        },
        { status: 410 }
      );
    }

    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app';
    const activationUrl = `${baseUrl}/activate?code=${existingCode.code}`;

    // Try to resend activation email
    let emailSent = false;
    let emailError = null;
    
    try {
      const resendResponse = await fetch(`${baseUrl}/api/send-activation-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          code: existingCode.code,
          activationUrl,
          productName: 'Premium Tier'
        })
      });

      if (resendResponse.ok) {
        emailSent = true;
      } else {
        const errorData = await resendResponse.json().catch(() => ({}));
        emailError = errorData.error || 'Email service unavailable';
        console.error('[ActivationCode] Email send failed:', emailError);
      }
    } catch (emailErr) {
      emailError = emailErr.message;
      console.error('[ActivationCode] Email send error:', emailErr);
    }

    // Always return the code even if email fails (for testing/debugging)
    return NextResponse.json({
      success: true,
      message: emailSent 
        ? 'Activation email resent successfully' 
        : 'Email sending failed, but here is your activation code',
      code: existingCode.code,
      activationUrl,
      emailSent,
      ...(emailError && { emailError, hint: 'You can use the activation URL directly' }),
    });
  } catch (error) {
    console.error('[ActivationCode] Error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to resend activation code',
        details: error.message 
      },
      { status: 500 }
    );
  }
}
