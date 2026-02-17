/**
 * Polar Webhook Handler
 * 
 * Simple webhook endpoint that forwards to the main handler
 * This works with the current static site setup
 */

export default async function handler(req, res) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const body = req.body;
    const eventType = body?.type;
    const eventData = body?.data;

    console.log(`[Webhook] Received: ${eventType}`);

    // Handle different event types
    switch (eventType) {
      case 'checkout.completed':
        return handleCheckoutCompleted(eventData, res);
      
      case 'subscription.created':
      case 'subscription.active':
        return handleSubscriptionCreated(eventData, res);
      
      case 'subscription.canceled':
        return handleSubscriptionCanceled(eventData, res);
      
      case 'subscription.updated':
        return handleSubscriptionUpdated(eventData, res);
      
      case 'refund.created':
      case 'refund.succeeded':
        return handleRefund(eventData, res);
      
      default:
        console.log(`[Webhook] Unknown event: ${eventType}`);
        return res.status(200).json({ received: true, skipped: true });
    }
  } catch (error) {
    console.error('[Webhook] Error:', error);
    return res.status(500).json({ error: 'Internal error' });
  }
}

function generateCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 8; i++) {
    if (i === 4) code += '-';
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

function generateToken() {
  return 'pbs_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

async function handleCheckoutCompleted(data, res) {
  const email = data?.customer_email || data?.customer?.email;
  const checkoutId = data?.id;
  
  if (!email) {
    return res.status(400).json({ error: 'No email' });
  }

  // Generate activation code
  const code = generateCode();
  const token = generateToken();

  console.log(`[Checkout] Created: ${code} for ${email}`);

  // Send activation email
  try {
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://power-benchmarking-week2.vercel.app';
    const activationUrl = `${baseUrl}/activate?code=${code}`;
    
    await fetch(`${baseUrl}/api/send-activation-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        code,
        activationUrl,
        productName: data?.product?.name || 'Premium'
      })
    });
  } catch (e) {
    console.log('[Email] Failed:', e.message);
  }

  return res.status(200).json({ 
    success: true, 
    checkoutId,
    message: 'Activation code created' 
  });
}

async function handleSubscriptionCreated(data, res) {
  const email = data?.customer?.email;
  const subId = data?.id;
  
  if (!email) {
    return res.status(200).json({ received: true });
  }

  const code = generateCode();
  console.log(`[Subscription] Created: ${code} for ${email}`);

  return res.status(200).json({ success: true });
}

async function handleSubscriptionCanceled(data, res) {
  console.log(`[Subscription] Canceled: ${data?.id}`);
  return res.status(200).json({ success: true });
}

async function handleSubscriptionUpdated(data, res) {
  console.log(`[Subscription] Updated: ${data?.id}, status: ${data?.status}`);
  return res.status(200).json({ success: true });
}

async function handleRefund(data, res) {
  console.log(`[Refund] ${data?.id}`);
  return res.status(200).json({ success: true });
}
