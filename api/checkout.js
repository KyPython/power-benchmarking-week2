export default function handler(req, res) {
  const plan = req.query?.plan || 'premium';
  const premium = process.env.POLAR_PREMIUM_URL || process.env.POLAR_CHECKOUT_URL;
  const enterprise = process.env.POLAR_ENTERPRISE_URL;
  const free = process.env.POLAR_FREE_URL;
  let url = premium;
  if (plan === 'enterprise') {
    url = enterprise;
  } else if (plan === 'free') {
    url = free;
  }
  if (!url) {
    res.status(500).json({ error: `Checkout URL not set for plan=${plan}` });
    return;
  }
  res.writeHead(302, { Location: url });
  res.end();
}
