'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function SuccessPage({ searchParams }) {
  const checkoutId = searchParams?.checkout_id || null;
  const [code, setCode] = useState(null);
  const [loading, setLoading] = useState(false);

  // In production, we'd get the code from the checkout session
  // For now, show instructions for both flows
  
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
          <a href="mailto:support@example.com" style={styles.link}>
            support@example.com
          </a>
        </p>
      </div>
    </main>
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
};
