'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

function ActivateContent() {
  const searchParams = useSearchParams();
  const code = searchParams.get('code');
  
  const [status, setStatus] = useState('loading');
  const [deviceData, setDeviceData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (code) {
      checkCode();
    } else {
      setStatus('error');
      setError('No activation code provided');
    }
  }, [code]);

  async function checkCode() {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || '';
      const res = await fetch(`${baseUrl}/api/device-codes/${code}`);
      
      if (!res.ok) {
        throw new Error('Invalid or expired code');
      }
      
      const data = await res.json();
      setDeviceData(data);
      
      if (data.activated) {
        setStatus('success');
      } else {
        setStatus('found');
      }
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  }

  async function handleActivate() {
    setStatus('activating');
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || '';
      const res = await fetch(`${baseUrl}/api/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, confirm: true })
      });
      
      if (!res.ok) {
        throw new Error('Activation failed');
      }
      
      const data = await res.json();
      setDeviceData({ ...deviceData, ...data, activated: true });
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  }

  if (status === 'loading') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.spinner}></div>
          <p>Loading activation code...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h1 style={{ color: '#dc2626' }}>Activation Error</h1>
          <p>{error || 'Something went wrong'}</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.successIcon}>✓</div>
          <h1 style={{ color: '#16a34a' }}>Activation Complete!</h1>
          <p>Your premium features are now enabled.</p>
          <a href="/" style={styles.button}>Go to Home</a>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1>Activate Premium</h1>
        <p>You've received a premium activation code.</p>
        <div style={styles.codeBox}>
          <code style={styles.code}>{code}</code>
        </div>
        <button onClick={handleActivate} style={styles.activateButton}>
          Activate Now
        </button>
      </div>
    </div>
  );
}

export default function ActivatePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ActivateContent />
    </Suspense>
  );
}

const styles = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb', padding: '20px' },
  card: { backgroundColor: 'white', borderRadius: '12px', padding: '40px', maxWidth: '400px', width: '100%', textAlign: 'center', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' },
  spinner: { width: '40px', height: '40px', border: '3px solid #e5e7eb', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 20px' },
  codeBox: { backgroundColor: '#f3f4f6', padding: '16px', borderRadius: '8px', margin: '20px 0' },
  code: { fontSize: '24px', fontWeight: 'bold', letterSpacing: '2px' },
  activateButton: { backgroundColor: '#2563eb', color: 'white', border: 'none', padding: '14px 28px', fontSize: '16px', borderRadius: '8px', cursor: 'pointer', width: '100%', fontWeight: '600' },
  button: { display: 'inline-block', backgroundColor: '#2563eb', color: 'white', padding: '12px 24px', borderRadius: '8px', textDecoration: 'none', marginTop: '20px', fontWeight: '600' },
  successIcon: { width: '60px', height: '60px', backgroundColor: '#dcfce7', color: '#16a34a', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '30px', margin: '0 auto 20px' },
};
