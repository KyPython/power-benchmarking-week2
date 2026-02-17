export default function SuccessPage({ searchParams }) {
  const checkoutId = searchParams?.checkout_id || null;
  return (
    <main style={{ padding: 32, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial' }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Thanks for your purchase!</h1>
      {checkoutId ? (
        <p style={{ color: '#374151' }}>Checkout ID: <code>{checkoutId}</code></p>
      ) : (
        <p style={{ color: '#6b7280' }}>Purchase completed.</p>
      )}
      <p style={{ marginTop: 16, color: '#6b7280' }}>
        In the CLI, run: <code>power-benchmark premium verify</code> to enable premium.
      </p>
    </main>
  );
}
