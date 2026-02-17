import Link from 'next/link';

export const metadata = {
  title: 'Power Benchmarking Suite',
  description: 'Monitor and analyze power consumption on Apple Silicon Macs',
};

export default function HomePage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      padding: '2rem',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem', fontWeight: 700 }}>
        Power Benchmarking Suite
      </h1>
      <p style={{ fontSize: '1.3rem', marginBottom: '2.5rem', textAlign: 'center', opacity: 0.95, maxWidth: '600px' }}>
        Monitor and analyze power consumption on Apple Silicon Macs
      </p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link 
          href="/activate" 
          style={{
            background: 'white',
            color: '#007AFF',
            padding: '16px 32px',
            borderRadius: '30px',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '18px',
            transition: 'transform 0.3s'
          }}
        >
          Activate Premium
        </Link>
        <a 
          href="https://power-benchmarking-week2.vercel.app/docs/pricing.html" 
          style={{
            background: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            padding: '16px 32px',
            borderRadius: '30px',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '18px',
            border: '2px solid white'
          }}
        >
          View Pricing
        </a>
      </div>
    </div>
  );
}
