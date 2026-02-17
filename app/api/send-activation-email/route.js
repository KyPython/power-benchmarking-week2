/**
 * Send Activation Email API
 * 
 * POST /api/send-activation-email
 * Sends activation email after purchase
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { email, code, activationUrl, productName } = await request.json();

    if (!email || !code) {
      return NextResponse.json(
        { error: 'Email and code are required' },
        { status: 400 }
      );
    }

    const sgMail = require('@sendgrid/mail');
    const apiKey = process.env.SENDGRID_API_KEY;
    
    if (!apiKey) {
      console.log('[Email] No SENDGRID_API_KEY configured');
      return NextResponse.json(
        { error: 'Email service not configured' },
        { status: 500 }
      );
    }

    sgMail.setApiKey(apiKey);

    const msg = {
      to: email,
      from: process.env.FROM_EMAIL || 'noreply@power-benchmarking.com',
      subject: '🎉 Your Premium is Ready - Activate Now',
      html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Activate Your Premium</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; text-align: center; color: white;">
      <h1 style="margin: 0; font-size: 28px;">🎉 Thanks for Your Purchase!</h1>
      <p style="margin: 10px 0 0 0; opacity: 0.9;">${productName || 'Power Benchmarking Premium'}</p>
    </div>
    
    <div style="padding: 30px; background: #f9fafb; border-radius: 12px; margin-top: 20px;">
      <p>Hi there!</p>
      <p>Your premium subscription is ready. Activate it now to unlock:</p>
      <ul style="text-align: left;">
        <li>🚀 Unlimited monitoring sessions</li>
        <li>📊 Advanced analytics</li>
        <li>☁️ Cloud sync (coming soon)</li>
      </ul>
      
      <div style="text-align: center; margin: 30px 0;">
        <a href="${activationUrl}" style="background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
          Activate Premium
        </a>
      </div>
      
      <p style="font-size: 14px; color: #666;">
        Or copy this code: <strong style="font-family: monospace; font-size: 16px;">${code}</strong>
      </p>
      
      <p style="font-size: 14px; color: #666; margin-top: 30px;">
        Activation link expires in 15 minutes.
      </p>
    </div>
    
    <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
      Need help? Reply to this email or visit our <a href="https://github.com" style="color: #667eea;">docs</a>.
    </p>
  </body>
</html>
      `,
    };

    await sgMail.send(msg);
    
    console.log('[Email] Activation email sent to:', email);
    return NextResponse.json({ success: true });
    
  } catch (error) {
    console.error('[Email] Error:', error);
    return NextResponse.json(
      { error: 'Failed to send email' },
      { status: 500 }
    );
  }
}
