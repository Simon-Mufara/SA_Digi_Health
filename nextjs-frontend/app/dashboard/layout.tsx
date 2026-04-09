'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { checkHealth } from '@/lib/api';

type UserRole = 'doctor' | 'clinician' | 'admin' | 'security_officer' | 'researcher';

interface NavItem {
  label: string;
  href: string;
  icon: string;
}

const roleNavItems: Record<UserRole, NavItem[]> = {
  doctor: [
    { label: 'Overview', href: '/dashboard/doctor', icon: '🏠' },
    { label: 'Patients', href: '/dashboard/doctor/patients', icon: '👥' },
    { label: 'Schedule', href: '/dashboard/doctor/schedule', icon: '📅' },
    { label: 'AI Summaries', href: '/dashboard/doctor/ai', icon: '🤖' },
  ],
  clinician: [
    { label: 'Overview', href: '/dashboard/clinician', icon: '🏠' },
    { label: 'Patient Intake', href: '/dashboard/clinician/intake', icon: '📋' },
    { label: 'Vitals Entry', href: '/dashboard/clinician/vitals', icon: '💓' },
    { label: 'Sessions', href: '/dashboard/clinician/sessions', icon: '🎫' },
  ],
  admin: [
    { label: 'Overview', href: '/dashboard/admin', icon: '🏠' },
    { label: 'Staff', href: '/dashboard/admin/staff', icon: '👤' },
    { label: 'Roles', href: '/dashboard/admin/roles', icon: '🔐' },
    { label: 'System', href: '/dashboard/admin/system', icon: '⚙️' },
  ],
  security_officer: [
    { label: 'Overview', href: '/dashboard/security', icon: '🏠' },
    { label: 'Live Feed', href: '/dashboard/security/live', icon: '📡' },
    { label: 'Audit Log', href: '/dashboard/security/audit', icon: '📜' },
    { label: 'Alerts', href: '/dashboard/security/alerts', icon: '🚨' },
  ],
  researcher: [
    { label: 'Overview', href: '/dashboard/research', icon: '🏠' },
    { label: 'Cohorts', href: '/dashboard/research/cohorts', icon: '📊' },
    { label: 'Charts', href: '/dashboard/research/charts', icon: '📈' },
    { label: 'Export', href: '/dashboard/research/export', icon: '💾' },
  ],
};

const roleColors: Record<UserRole, string> = {
  doctor: '#8b5cf6',
  clinician: '#06b6d4',
  admin: '#f59e0b',
  security_officer: '#ef4444',
  researcher: '#10b981',
};

const roleLabels: Record<UserRole, string> = {
  doctor: 'Doctor',
  clinician: 'Clinician',
  admin: 'Admin',
  security_officer: 'Security',
  researcher: 'Researcher',
};

function Sidebar({ staffId, role }: { staffId: string; role: UserRole }) {
  const pathname = usePathname();
  const router = useRouter();
  const [tokenExpiry, setTokenExpiry] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState<string>('');

  const navItems = roleNavItems[role] || [];
  const roleColor = roleColors[role] || '#6b7280';
  const roleLabel = roleLabels[role] || role;

  useEffect(() => {
    // Parse JWT from cookie to get expiry (client-side demo)
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(';').shift();
    };
    
    const token = getCookie('access_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setTokenExpiry(payload.exp * 1000);
      } catch {}
    }
  }, []);

  useEffect(() => {
    if (!tokenExpiry) return;
    
    const interval = setInterval(() => {
      const remaining = tokenExpiry - Date.now();
      if (remaining <= 0) {
        setTimeLeft('Expired');
        return;
      }
      const mins = Math.floor(remaining / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);
      setTimeLeft(`${mins}:${secs.toString().padStart(2, '0')}`);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [tokenExpiry]);

  const handleLogout = async () => {
    try {
      await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });
    } catch {}
    // Clear cookies client-side
    document.cookie = 'access_token=; Max-Age=0; path=/';
    document.cookie = 'refresh_token=; Max-Age=0; path=/';
    router.push('/login');
  };

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      height: '100vh',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      left: 0,
      top: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 8,
            background: `linear-gradient(135deg, var(--accent), ${roleColor})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            fontWeight: 700,
            color: 'var(--bg-primary)',
          }}>
            Y
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1.1rem' }}>South African DigiHealth</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Biometric Health System
            </div>
          </div>
        </div>
      </div>

      {/* User info */}
      <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
          Logged in as
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, marginBottom: '0.5rem' }}>
          {staffId}
        </div>
        <span 
          className="role-badge"
          style={{
            background: `${roleColor}20`,
            color: roleColor,
          }}
        >
          {roleLabel}
        </span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0.75rem', overflow: 'auto' }}>
        {navItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== `/dashboard/${role}` && pathname.startsWith(item.href));
          
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: 8,
                marginBottom: '0.25rem',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                background: isActive ? 'var(--accent-muted)' : 'transparent',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: isActive ? 500 : 400,
                transition: 'all 0.15s',
              }}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Session timer */}
      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
          Session expires in
        </div>
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: '1.25rem', 
          fontWeight: 500,
          color: timeLeft === 'Expired' ? 'var(--danger)' : 'var(--accent)',
        }}>
          {timeLeft || '--:--'}
        </div>
      </div>

      {/* Logout */}
      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ width: '100%' }}
        >
          🚪 Logout
        </button>
      </div>
    </aside>
  );
}

function Topbar() {
  const pathname = usePathname();
  const [time, setTime] = useState<string>('');
  const [isHealthy, setIsHealthy] = useState<boolean>(true);

  useEffect(() => {
    const updateTime = () => {
      setTime(new Date().toLocaleTimeString('en-ZA', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
      }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const checkStatus = async () => {
      const healthy = await checkHealth();
      setIsHealthy(healthy);
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Generate breadcrumb from path
  const pathParts = pathname.split('/').filter(Boolean);
  const breadcrumb = pathParts.map((part, i) => ({
    label: part.charAt(0).toUpperCase() + part.slice(1).replace('-', ' '),
    href: '/' + pathParts.slice(0, i + 1).join('/'),
    isLast: i === pathParts.length - 1,
  }));

  return (
    <header style={{
      height: 'var(--topbar-height)',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.5rem',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Breadcrumb */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {breadcrumb.map((item, i) => (
          <span key={item.href} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {i > 0 && <span style={{ color: 'var(--text-muted)' }}>/</span>}
            {item.isLast ? (
              <span style={{ fontWeight: 500 }}>{item.label}</span>
            ) : (
              <Link 
                href={item.href}
                style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}
              >
                {item.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        {/* System status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span 
            className="status-dot"
            style={{ 
              background: isHealthy ? 'var(--success)' : 'var(--danger)',
              boxShadow: isHealthy ? '0 0 6px var(--success)' : '0 0 6px var(--danger)',
            }}
          />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {isHealthy ? 'System Online' : 'System Offline'}
          </span>
        </div>

        {/* Clock */}
        <div style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: '0.9rem',
          color: 'var(--text-secondary)',
        }}>
          {time}
        </div>
      </div>
    </header>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [staffId, setStaffId] = useState<string>('');
  const [role, setRole] = useState<UserRole>('clinician');

  useEffect(() => {
    // Parse JWT from cookie (client-side)
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(';').shift();
    };
    
    const token = getCookie('access_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setStaffId(payload.sub || '');
        setRole(payload.role || 'clinician');
      } catch {}
    }
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar staffId={staffId} role={role} />
      <div style={{ 
        flex: 1, 
        marginLeft: 'var(--sidebar-width)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <Topbar />
        <main style={{ flex: 1, padding: '1.5rem', overflow: 'auto' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
