'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';

function SuccessContent() {
  const searchParams = useSearchParams();
  const checkoutId = searchParams?.get('checkout_id') || null;
  const email = searchParams?.get('email') || null;
  
  const [resendStatus, setResendStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleResendCode() {
    if (!email) {
      // Prompt for email if not in URL
      const userEmail = prompt('Please enter your email address:');
      if (!userEmail) return;
      return handleResendCodeWithEmail(userEmail);
    }
    return handleResendCodeWithEmail(email);
  }

  async function handleResendCodeWithEmail(userEmail) {
    setLoading(true);
    setResendStatus(null);
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || window.location.origin;
      const res = await fetch(`${baseUrl}/api/activation-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setResendStatus({ type: 'success', message: 'Activation code resent! Check your email.' });
      } else {
        setResendStatus({ type: 'error', message: data.error || 'Failed to resend code' });
      }
    } catch (err) {
      setResendStatus({ type: 'error', message: 'Failed to resend activation code' });
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <main style={styles.container}>
      <h1 style={styles.title}>Thanks for your purchase! 🎉</h1>
      
      {checkoutId && (
        <p style={styles.checkoutId}>
          Checkout ID: <code>{checkoutId}</code>
        </p>
      )}
      
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>How to Activate</h2>
        
        <div style={styles.option}>
          <h3 style={styles.optionTitle}>Option 1: Automatic Activation (Recommended)</h3>
          <p style={styles.optionDesc}>
            Check your email for an activation link. Click it to automatically enable premium features.
          </p>
          {email && (
            <button 
              onClick={handleResendCode}
              disabled={loading}
              style={styles.resendButton}
            >
              {loading ? 'Sending...' : '📧 Resend Activation Email'}
            </button>
          )}
          {!email && (
            <button 
              onClick={handleResendCode}
              disabled={loading}
              style={styles.resendButton}
            >
              {loading ? 'Sending...' : '📧 Resend Activation Email'}
            </button>
          )}
          {resendStatus && (
            <p style={{
              ...styles.statusMessage,
              color: resendStatus.type === 'success' ? '#16a34a' : '#dc2626'
            }}>
              {resendStatus.message}
            </p>
          )}
        </div>
        
        <div style={styles.option}>
          <h3 style={styles.optionTitle}>Option 2: Device-Link Activation</h3>
          <p style={styles.optionDesc}>
            Run this command in your terminal:
          </p>
          <pre style={styles.code}>
            power-benchmark premium login --device
          </pre>
          <p style={styles.optionDesc}>
            Then visit the URL shown to confirm activation.
          </p>
        </div>
        
        <div style={styles.option}>
          <h3 style={styles.optionTitle}>Option 3: Manual Token</h3>
          <p style={styles.optionDesc}>
            If you have a license token, run:
          </p>
          <pre style={styles.code}>
            power-benchmark premium login --token YOUR_TOKEN
          </pre>
        </div>
      </div>
      
      <div style={styles.help}>
        <p>
          Need help? Contact us at{' '}
          <a href="mailto:kyjahntsmith@gmail.com" style={styles.link}>
            kyjahntsmith@gmail.com
          </a>
        </p>
      </div>
    </main>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div style={styles.container}>Loading...</div>}>
      <SuccessContent />
    </Suspense>
  );
}

const styles = {
  container: {
    padding: '32px',
    fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
    maxWidth: '600px',
    margin: '0 auto',
  },
  title: {
    fontSize: '28px',
    marginBottom: '16px',
    color: '#111827',
  },
  checkoutId: {
    color: '#6b7280',
    marginBottom: '24px',
  },
  card: {
    backgroundColor: 'white',
    border: '1px solid #e5e7eb',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
  },
  cardTitle: {
    fontSize: '20px',
    marginBottom: '16px',
    color: '#111827',
  },
  option: {
    marginBottom: '20px',
    paddingBottom: '20px',
    borderBottom: '1px solid #e5e7eb',
  },
  optionTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
    marginBottom: '8px',
  },
  optionDesc: {
    color: '#6b7280',
    marginBottom: '8px',
    lineHeight: '1.5',
  },
  code: {
    backgroundColor: '#f3f4f6',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '14px',
    overflow: 'x-auto',
    color: '#374151',
    fontFamily: 'ui-monospace, monospace',
  },
  help: {
    color: '#6b7280',
    fontSize: '14px',
    textAlign: 'center',
  },
  link: {
    color: '#2563eb',
    textDecoration: 'underline',
  },
  resendButton: {
    backgroundColor: '#667eea',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    marginTop: '12px',
    transition: 'background-color 0.2s',
  },
  statusMessage: {
    marginTop: '12px',
    fontSize: '14px',
    fontWeight: '500',
  },
};
