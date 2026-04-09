'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

interface AuditEvent {
  id: string;
  timestamp: string;
  staff_id: string;
  action: string;
  ip: string;
  outcome: 'success' | 'fail' | 'role_mismatch';
  details?: string;
}

interface FailedAuthEntry {
  id: string;
  timestamp: string;
  staff_id: string;
  ip: string;
  reason: string;
  role_attempted?: string;
}

interface AlertItem {
  staff_id: string;
  failed_count: number;
  last_attempt: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

// Mock data generator for live feed demo
function generateMockEvent(): AuditEvent {
  const actions = ['login', 'logout', 'access_patient', 'create_session', 'export_data', 'role_request'];
  const outcomes: AuditEvent['outcome'][] = ['success', 'success', 'success', 'fail', 'role_mismatch'];
  const staffIds = ['DR-001', 'CLIN-001', 'ADM-001', 'SEC-001', 'RES-001', 'DR-002', 'UNKNOWN'];
  
  return {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    staff_id: staffIds[Math.floor(Math.random() * staffIds.length)],
    action: actions[Math.floor(Math.random() * actions.length)],
    ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
    outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
  };
}

const mockFailedAuth: FailedAuthEntry[] = [
  { id: '1', timestamp: '2025-01-27 08:45:23', staff_id: 'DR-003', ip: '192.168.1.45', reason: 'Invalid password', role_attempted: 'doctor' },
  { id: '2', timestamp: '2025-01-27 07:30:12', staff_id: 'UNKNOWN', ip: '10.0.0.55', reason: 'Staff ID not found', role_attempted: 'admin' },
  { id: '3', timestamp: '2025-01-27 06:15:45', staff_id: 'CLIN-001', ip: '192.168.1.100', reason: 'Role mismatch', role_attempted: 'doctor' },
  { id: '4', timestamp: '2025-01-26 23:45:00', staff_id: 'DR-002', ip: '192.168.1.77', reason: 'Invalid password' },
  { id: '5', timestamp: '2025-01-26 22:10:33', staff_id: 'SEC-001', ip: '192.168.1.12', reason: 'Session expired' },
];

const mockAlerts: AlertItem[] = [
  { staff_id: 'DR-003', failed_count: 5, last_attempt: '2025-01-27 08:45' },
  { staff_id: 'UNKNOWN', failed_count: 3, last_attempt: '2025-01-27 07:30' },
];

function StatsRow({ events }: { events: AuditEvent[] }) {
  const successCount = events.filter(e => e.outcome === 'success').length;
  const failCount = events.filter(e => e.outcome === 'fail').length;
  const mismatchCount = events.filter(e => e.outcome === 'role_mismatch').length;
  
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total Events (Live)</div>
        <div className="stat-value">{events.length}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Successful</div>
        <div className="stat-value" style={{ color: 'var(--success)' }}>{successCount}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Failed Auth</div>
        <div className="stat-value" style={{ color: 'var(--danger)' }}>{failCount}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Role Mismatch</div>
        <div className="stat-value" style={{ color: 'var(--warning)' }}>{mismatchCount}</div>
      </div>
    </div>
  );
}

function LiveEventFeed({ events }: { events: AuditEvent[] }) {
  const feedRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [events]);

  const getOutcomeStyle = (outcome: AuditEvent['outcome']) => {
    switch (outcome) {
      case 'success':
        return { color: 'var(--success)', bg: 'rgba(16, 185, 129, 0.1)' };
      case 'fail':
        return { color: 'var(--danger)', bg: 'rgba(239, 68, 68, 0.1)' };
      case 'role_mismatch':
        return { color: 'var(--warning)', bg: 'rgba(245, 158, 11, 0.1)' };
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>📡 Live Access Events</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="status-dot online" />
          <span className="text-sm text-muted">Connected</span>
        </div>
      </div>
      
      <div 
        ref={feedRef}
        style={{ 
          maxHeight: 400, 
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}
      >
        {events.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Waiting for events...
          </div>
        ) : (
          events.map(event => {
            const style = getOutcomeStyle(event.outcome);
            return (
              <div
                key={event.id}
                style={{
                  padding: '0.75rem',
                  background: style.bg,
                  borderRadius: 8,
                  borderLeft: `3px solid ${style.color}`,
                  animation: 'fadeIn 0.3s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span className="font-mono text-sm">{event.staff_id}</span>
                  <span className="text-xs text-muted">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{event.action}</span>
                  <span style={{ 
                    fontSize: '0.75rem', 
                    padding: '0.125rem 0.5rem',
                    borderRadius: 4,
                    background: style.color,
                    color: 'white',
                    fontWeight: 500,
                  }}>
                    {event.outcome.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>
                  IP: {event.ip}
                </div>
              </div>
            );
          })
        )}
      </div>
      
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function FailedAuthLog({ entries }: { entries: FailedAuthEntry[] }) {
  const [filter, setFilter] = useState('');
  
  const filteredEntries = entries.filter(e => 
    !filter || 
    e.staff_id.toLowerCase().includes(filter.toLowerCase()) ||
    e.ip.includes(filter) ||
    e.reason.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="card">
      <div className="card-header">
        <h3>🚫 Failed Auth Log (24h)</h3>
      </div>
      
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          className="input"
          placeholder="Filter by staff ID, IP, or reason..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>
      
      <table className="table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Staff ID</th>
            <th>IP</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {filteredEntries.map(entry => (
            <tr key={entry.id}>
              <td className="font-mono text-sm">{entry.timestamp}</td>
              <td>
                <span className={entry.staff_id === 'UNKNOWN' ? 'text-muted' : ''}>
                  {entry.staff_id}
                </span>
              </td>
              <td className="font-mono text-sm">{entry.ip}</td>
              <td>
                <span style={{ 
                  color: entry.reason === 'Role mismatch' ? 'var(--warning)' : 'var(--danger)',
                }}>
                  {entry.reason}
                </span>
                {entry.role_attempted && (
                  <span className="text-muted text-xs"> (tried: {entry.role_attempted})</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AlertPanel({ alerts }: { alerts: AlertItem[] }) {
  if (alerts.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>🚨 Security Alerts</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No active alerts
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ borderColor: 'var(--danger)' }}>
      <div className="card-header">
        <h3>🚨 Security Alerts</h3>
        <span className="chip chip-error">{alerts.length} active</span>
      </div>
      
      {alerts.map(alert => (
        <div 
          key={alert.staff_id}
          style={{
            padding: '1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: 8,
            marginBottom: '0.75rem',
            border: '1px solid rgba(239, 68, 68, 0.3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span className="font-mono" style={{ fontWeight: 600 }}>{alert.staff_id}</span>
            <span style={{ color: 'var(--danger)', fontWeight: 600 }}>
              {alert.failed_count} failed attempts
            </span>
          </div>
          <div className="text-sm text-muted">
            Last attempt: {alert.last_attempt}
          </div>
          <button 
            className="btn btn-danger"
            style={{ marginTop: '0.75rem', padding: '0.375rem 0.75rem' }}
          >
            Lock Account
          </button>
        </div>
      ))}
    </div>
  );
}

function ExportControls() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    
    // Simulate export
    await new Promise(r => setTimeout(r, 1500));
    
    // Create fake CSV download
    const csv = 'timestamp,staff_id,action,ip,outcome\n2025-01-27 08:00:00,DR-001,login,192.168.1.10,success';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${dateFrom || 'all'}-${dateTo || 'now'}.csv`;
    a.click();
    
    setExporting(false);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>💾 Export Audit Log</h3>
      </div>
      
      <div className="grid-2" style={{ gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <label className="label">From Date</label>
          <input
            type="date"
            className="input"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div>
          <label className="label">To Date</label>
          <input
            type="date"
            className="input"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </div>
      
      <button 
        className="btn btn-primary"
        onClick={handleExport}
        disabled={exporting}
        style={{ width: '100%' }}
      >
        {exporting ? '⏳ Generating CSV...' : '📥 Download CSV'}
      </button>
    </div>
  );
}

export default function SecurityDashboard() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Simulate WebSocket connection with mock data
  useEffect(() => {
    setConnected(true);
    
    // Add initial events
    const initial: AuditEvent[] = [];
    for (let i = 0; i < 5; i++) {
      initial.push(generateMockEvent());
    }
    setEvents(initial);
    
    // Simulate live events
    const interval = setInterval(() => {
      if (Math.random() > 0.3) {
        setEvents(prev => [generateMockEvent(), ...prev].slice(0, 50));
      }
    }, 3000);
    
    return () => {
      clearInterval(interval);
      setConnected(false);
    };
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Security Dashboard</h1>
        <p className="text-muted">Monitor access events and security alerts in real-time</p>
      </div>

      <StatsRow events={events} />

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        <LiveEventFeed events={events} />
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <AlertPanel alerts={mockAlerts} />
          <ExportControls />
        </div>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <FailedAuthLog entries={mockFailedAuth} />
      </div>
    </div>
  );
}
