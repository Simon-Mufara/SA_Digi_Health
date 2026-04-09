'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/');
  }, [router]);
  
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0f1e',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#9ca3af',
    }}>
      <div>Redirecting...</div>
    </div>
  );
}
