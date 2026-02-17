export default function PricingPage() {
  return (
    <main style={{ padding: 32, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial' }}>
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>Power Benchmarking Suite — Pricing</h1>
      <p style={{ color: '#555', marginBottom: 24 }}>
        Choose a plan. Checkout is powered by Polar. After purchase, the app unlocks premium automatically.
      </p>
      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Free</h2>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            <li>1 device</li>
            <li>Up to 1 hour per session</li>
            <li>Basic analytics</li>
          </ul>
        </section>
        <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Premium</h2>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            <li>Unlimited benchmarking</li>
            <li>Cloud sync</li>
            <li>Team collaboration</li>
            <li>Advanced analytics</li>
          </ul>
          <a href="/api/checkout" style={{
            display: 'inline-block', marginTop: 12, padding: '10px 14px',
            backgroundColor: '#111827', color: '#fff', borderRadius: 6, textDecoration: 'none'
          }}>Buy Premium</a>
        </section>
        <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Enterprise</h2>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            <li>Custom limits</li>
            <li>SLAs and support</li>
            <li>Security reviews</li>
          </ul>
          <a href="mailto:sales@modelogic.dev" style={{
            display: 'inline-block', marginTop: 12, padding: '10px 14px',
            backgroundColor: '#2563eb', color: '#fff', borderRadius: 6, textDecoration: 'none'
          }}>Contact Sales</a>
        </section>
      </div>
      <p style={{ marginTop: 24, color: '#6b7280' }}>
        Already purchased? In the CLI, run: <code>power-benchmark premium verify</code>
      </p>
    </main>
  );
}
