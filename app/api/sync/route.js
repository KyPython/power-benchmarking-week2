/**
 * Sync API - Cloud sync for runs and entitlement checking
 * 
 * POST /api/sync - Save a run to the cloud
 * GET /api/sync - Get user's runs
 */

import { NextRequest, NextResponse } from 'next/server';
import { getUserByEmail, getEntitlement, saveRun, getRuns } from '../../../lib/supabase';

export async function POST(request) {
  try {
    const { email, run, token } = await request.json();

    if (!email || !run) {
      return NextResponse.json(
        { error: 'Email and run data required' },
        { status: 400 }
      );
    }

    // Get or create user
    const user = await getUserByEmail(email);
    
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Save the run
    const savedRun = await saveRun(user.id, run);

    return NextResponse.json({
      success: true,
      run: savedRun
    });
  } catch (error) {
    console.error('[Sync] Error:', error);
    return NextResponse.json(
      { error: 'Sync failed' },
      { status: 500 }
    );
  }
}

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get('email');

    if (!email) {
      return NextResponse.json(
        { error: 'Email required' },
        { status: 400 }
      );
    }

    const user = await getUserByEmail(email);
    
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    const runs = await getRuns(user.id);

    return NextResponse.json({
      runs
    });
  } catch (error) {
    console.error('[Sync] Error:', error);
    return NextResponse.json(
      { error: 'Failed to get runs' },
      { status: 500 }
    );
  }
}
