export default function handler(req, res) {
  const url = process.env.POLAR_CHECKOUT_URL;
  if (!url) {
    res.status(500).json({ error: "POLAR_CHECKOUT_URL not set" });
    return;
  }
  res.writeHead(302, { Location: url });
  res.end();
}
