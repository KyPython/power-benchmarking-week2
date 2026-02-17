/**
 * Webhook Diagnostic Endpoint
 * 
 * GET /api/webhooks/polar/test
 * Check if webhook is configured correctly
 */

import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export async function GET() {
  const diagnostics = {
    timestamp: new Date().toISOString(),
    supabase: {
      configured: !!supabase,
      url: process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || 'NOT SET',
      key: process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'SET' : 'NOT SET',
    },
    polar: {
      webhookSecret: process.env.POLAR_WEBHOOK_SECRET ? 'SET' : 'NOT SET',
      accessToken: process.env.POLAR_ACCESS_TOKEN ? 'SET' : 'NOT SET',
    },
    email: {
      sendgrid: process.env.SENDGRID_API_KEY ? 'SET' : 'NOT SET',
      fromEmail: process.env.FROM_EMAIL || 'NOT SET',
    },
    database: {
      connected: false,
      error: null,
    },
  };

  // Test Supabase connection
  if (supabase) {
    try {
      const { data, error } = await supabase.from('users').select('count').limit(1);
      diagnostics.database.connected = !error;
      diagnostics.database.error = error?.message || null;
    } catch (e) {
      diagnostics.database.error = e.message;
    }
  }

  return NextResponse.json(diagnostics, {
    headers: {
      'Cache-Control': 'no-store',
    },
  });
}
