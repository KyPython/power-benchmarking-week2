# Automatic Feature Delivery

This document describes how Power Benchmarking Suite automatically delivers premium features to customers after purchase - **without requiring a database**.

## Overview

The system uses a **device-link / activation code** flow similar to Spotify or GitHub CLI:

1. Customer purchases via Polar checkout
2. Polar sends webhook to backend → creates activation code
3. Customer receives email with activation link
4. Customer clicks link → activation confirmed
5. CLI automatically picks up the license token

## Security Features

### Webhook Signature Verification
All webhook events are verified using HMAC-SHA256 signature validation:
- Timestamp check (prevents replay attacks within 5 min window)
- Constant-time comparison (prevents timing attacks)
- Rejects requests without valid signature

### Idempotency
- Duplicate webhook events are detected and ignored
- Each event is tracked by unique ID
- Prevents double-activation or double-charging

### Subscription Verification
- CLI verifies subscription with Polar API before enabling features
- Falls back to cached state on network failure
- Invalid tokens are cleared automatically

### Audit Trail
- All purchase events are logged
- Refund/cancellation events tracked
- Purchase records stored for reconciliation

## Architecture

### Components

- **Polar Checkout** - Payment processing
- **Webhook Handler** (`/api/webhooks/polar`) - Receives payment events
- **Device Codes API** (`/api/device-codes`) - Manages activation codes
- **Activation Page** (`/activate`) - Web UI for user confirmation
- **CLI Device Flow** (`premium login --device`) - Polls for activation

### No Database Required

The system uses:
- **In-memory storage** for device codes (server-side)
- **Local JSON files** for license tokens (client-side)
- **Polar API** for subscription verification

## How It Works

### 1. Purchase Flow

```
Customer → Polar Checkout → Webhook → Activation Code Created
                                         ↓
                                   Email Sent to Customer
```

### 2. Activation Flow (Two Options)

#### Option A: Email Link (Automatic)
```
Customer receives email with link
        ↓
Clicks "Activate Premium" link
        ↓
Activation confirmed on web
        ↓
CLI auto-detects (via polling or next run)
```

#### Option B: Device-Link (Interactive)
```
Customer runs: power-benchmark premium login --device
        ↓
Shows activation code + URL
        ↓
Customer visits URL in browser
        ↓
Confirms activation
        ↓
CLI receives token automatically
```

### 3. Feature Access

Once activated, the CLI checks:
1. `POLAR_API_KEY` environment variable
2. Local config file `~/.power_benchmarking/premium_config.json`
3. Falls back to Polar API verification

## API Endpoints

### POST /api/device-codes
Create a new activation code.

```bash
curl -X POST https://your-domain.com/api/device-codes \
  -H "Content-Type: application/json" \
  -d '{"email": "customer@example.com", "plan": "premium"}'
```

Response:
```json
{
  "code": "ABCD-1234",
  "expiresAt": 1700000000000,
  "verificationUrl": "https://your-domain.com/activate?code=ABCD-1234"
}
```

### GET /api/device-codes/[code]
Poll for activation status (CLI calls this).

```bash
curl https://your-domain.com/api/device-codes/ABCD-1234
```

Response (not activated):
```json
{
  "code": "ABCD-1234",
  "activated": false,
  "expiresAt": 1700000000000
}
```

Response (activated):
```json
{
  "code": "ABCD-1234",
  "activated": true,
  "expiresAt": 1700000000000,
  "token": "pbs_abc123..."
}
```

### POST /api/activate
Confirm device activation from web UI.

```bash
curl -X POST https://your-domain.com/api/activate \
  -H "Content-Type: application/json" \
  -d '{"code": "ABCD-1234", "confirm": true}'
```

### POST /api/webhooks/polar
Receive payment events from Polar.

## Environment Variables

Required for the web backend:

```bash
# Polar
POLAR_ACCESS_TOKEN=...
POLAR_WEBHOOK_SECRET=...
NEXT_PUBLIC_BASE_URL=https://your-domain.com

# Email (optional)
RESEND_API_KEY=...
FROM_EMAIL=support@your-domain.com

# CLI
POWER_BENCHMARK_API_URL=https://your-domain.com
```

## CLI Commands

### Check Premium Status
```bash
power-benchmark premium status
```

### Device-Link Activation
```bash
power-benchmark premium login --device
```

### Manual Token (fallback)
```bash
power-benchmark premium login --token YOUR_TOKEN
```

### Verify Entitlement
```bash
power-benchmark premium verify
```

### Upgrade
```bash
power-benchmark premium upgrade --open
```

## Security Considerations

1. **Activation codes expire** after 15 minutes
2. **License tokens** are tied to user email
3. **Webhook signature** verification (production)
4. **HTTPS required** for production deployment

## Production Setup

1. Deploy to Vercel or similar
2. Configure Polar webhook URL
3. Set environment variables
4. Test the full flow

## Troubleshooting

### "Code expired" error
- Activation codes are valid for 15 minutes
- Request a new code after purchase

### "Could not connect" error
- Check `POWER_BENCHMARK_API_URL` environment variable
- Ensure web server is running

### Features not enabled after activation
- Run `power-benchmark premium verify`
- Check `~/.power_benchmarking/premium_config.json`
