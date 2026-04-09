'use client';

import { useState, useEffect, useCallback } from 'react';

interface StaffMember {
  id: string;
  staff_id: string;
  name: string;
  role: string;
  status: 'active' | 'inactive';
  last_login: string;
}

interface RoleRequest {
  id: string;
  staff_id: string;
  current_role: string;
  requested_role: string;
  reason: string;
  created_at: string;
}

interface SystemHealth {
  database: 'healthy' | 'degraded' | 'down';
  redis: 'healthy' | 'degraded' | 'down';
  face_service: 'healthy' | 'degraded' | 'down';
  ai_service: 'healthy' | 'degraded' | 'down';
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

// Mock data
const mockStaff: StaffMember[] = [
  { id: '1', staff_id: 'DR-001', name: 'Dr. Sarah Nkosi', role: 'doctor', status: 'active', last_login: '2025-01-27 08:30' },
  { id: '2', staff_id: 'CLIN-001', name: 'Thabo Molefe', role: 'clinician', status: 'active', last_login: '2025-01-27 07:45' },
  { id: '3', staff_id: 'ADM-001', name: 'Naledi Khumalo', role: 'admin', status: 'active', last_login: '2025-01-27 09:00' },
  { id: '4', staff_id: 'SEC-001', name: 'Johannes van der Berg', role: 'security_officer', status: 'active', last_login: '2025-01-26 22:00' },
  { id: '5', staff_id: 'RES-001', name: 'Dr. Ahmed Patel', role: 'researcher', status: 'inactive', last_login: '2025-01-20 14:30' },
];

const mockRoleRequests: RoleRequest[] = [
  { id: '1', staff_id: 'CLIN-002', current_role: 'clinician', requested_role: 'admin', reason: 'Need admin access for reporting', created_at: '2025-01-25' },
];

function StatsRow() {
  const [stats, setStats] = useState({
    totalStaff: 0,
    activeSessions: 0,
    pendingRequests: 0,
    uptime: '99.9%',
  });

  useEffect(() => {
    setStats({
      totalStaff: mockStaff.length,
      activeSessions: 12,
      pendingRequests: mockRoleRequests.length,
      uptime: '99.9%',
    });
  }, []);

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total Staff</div>
        <div className="stat-value">{stats.totalStaff}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Active Sessions</div>
        <div className="stat-value" style={{ color: 'var(--info)' }}>{stats.activeSessions}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Pending Requests</div>
        <div className="stat-value" style={{ color: stats.pendingRequests > 0 ? 'var(--warning)' : 'var(--success)' }}>
          {stats.pendingRequests}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">System Uptime</div>
        <div className="stat-value" style={{ color: 'var(--success)' }}>{stats.uptime}</div>
      </div>
    </div>
  );
}

function StaffTable({
  staff,
  onDeactivate,
  onChangeRole,
}: {
  staff: StaffMember[];
  onDeactivate: (id: string) => void;
  onChangeRole: (id: string, newRole: string) => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newRole, setNewRole] = useState('');

  const roleLabels: Record<string, string> = {
    doctor: 'Doctor',
    clinician: 'Clinician',
    admin: 'Admin',
    security_officer: 'Security',
    researcher: 'Researcher',
  };

  const handleRoleChange = (id: string) => {
    if (newRole) {
      onChangeRole(id, newRole);
      setEditingId(null);
      setNewRole('');
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>👥 Staff Management</h3>
        <button className="btn btn-primary btn-sm">+ Add Staff</button>
      </div>
      
      <table className="table">
        <thead>
          <tr>
            <th>Staff ID</th>
            <th>Name</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last Login</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {staff.map(member => (
            <tr key={member.id}>
              <td>
                <span className="font-mono">{member.staff_id}</span>
              </td>
              <td>{member.name}</td>
              <td>
                {editingId === member.id ? (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select
                      className="select"
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                      style={{ width: 120, padding: '0.25rem' }}
                    >
                      <option value="">Select...</option>
                      <option value="doctor">Doctor</option>
                      <option value="clinician">Clinician</option>
                      <option value="admin">Admin</option>
                      <option value="security_officer">Security</option>
                      <option value="researcher">Researcher</option>
                    </select>
                    <button 
                      className="btn btn-primary"
                      style={{ padding: '0.25rem 0.5rem' }}
                      onClick={() => handleRoleChange(member.id)}
                    >
                      ✓
                    </button>
                    <button 
                      className="btn btn-ghost"
                      style={{ padding: '0.25rem 0.5rem' }}
                      onClick={() => setEditingId(null)}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <span className={`role-badge ${member.role}`}>
                    {roleLabels[member.role] || member.role}
                  </span>
                )}
              </td>
              <td>
                <span className={`chip ${member.status === 'active' ? 'chip-complete' : 'chip-error'}`}>
                  {member.status}
                </span>
              </td>
              <td className="font-mono text-sm text-muted">
                {member.last_login}
              </td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className="btn btn-ghost"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                    onClick={() => { setEditingId(member.id); setNewRole(member.role); }}
                  >
                    🔧 Role
                  </button>
                  <button 
                    className="btn btn-ghost"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', color: 'var(--danger)' }}
                    onClick={() => onDeactivate(member.id)}
                  >
                    🚫 {member.status === 'active' ? 'Deactivate' : 'Activate'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RoleRequestsQueue({
  requests,
  onApprove,
  onReject,
}: {
  requests: RoleRequest[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const roleLabels: Record<string, string> = {
    doctor: 'Doctor',
    clinician: 'Clinician',
    admin: 'Admin',
    security_officer: 'Security',
    researcher: 'Researcher',
  };

  if (requests.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>🔐 Role Requests</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No pending role change requests
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>🔐 Role Requests</h3>
        <span className="chip chip-waiting">{requests.length} pending</span>
      </div>
      
      {requests.map(request => (
        <div 
          key={request.id}
          style={{
            padding: '1rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span className="font-mono">{request.staff_id}</span>
            <span className="text-sm text-muted">{request.created_at}</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span className={`role-badge ${request.current_role}`}>
              {roleLabels[request.current_role]}
            </span>
            <span className="text-muted">→</span>
            <span className={`role-badge ${request.requested_role}`}>
              {roleLabels[request.requested_role]}
            </span>
          </div>
          
          <p className="text-sm text-muted" style={{ marginBottom: '0.75rem' }}>
            {request.reason}
          </p>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              className="btn btn-primary"
              style={{ padding: '0.375rem 0.75rem' }}
              onClick={() => onApprove(request.id)}
            >
              ✓ Approve
            </button>
            <button 
              className="btn btn-danger"
              style={{ padding: '0.375rem 0.75rem' }}
              onClick={() => onReject(request.id)}
            >
              ✕ Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function SystemHealthPanel() {
  const [health, setHealth] = useState<SystemHealth>({
    database: 'healthy',
    redis: 'healthy',
    face_service: 'healthy',
    ai_service: 'degraded',
  });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok) {
          setHealth(prev => ({ ...prev, database: 'healthy' }));
        } else {
          setHealth(prev => ({ ...prev, database: 'degraded' }));
        }
      } catch {
        setHealth(prev => ({ ...prev, database: 'down' }));
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: 'healthy' | 'degraded' | 'down') => {
    switch (status) {
      case 'healthy': return '🟢';
      case 'degraded': return '🟡';
      case 'down': return '🔴';
    }
  };

  const getStatusLabel = (status: 'healthy' | 'degraded' | 'down') => {
    switch (status) {
      case 'healthy': return 'Healthy';
      case 'degraded': return 'Degraded';
      case 'down': return 'Down';
    }
  };

  const services = [
    { key: 'database', label: 'Database (SQLite/PostgreSQL)' },
    { key: 'redis', label: 'Redis Cache' },
    { key: 'face_service', label: 'Face Recognition Service' },
    { key: 'ai_service', label: 'AI Summary Service' },
  ] as const;

  return (
    <div className="card">
      <div className="card-header">
        <h3>⚙️ System Health</h3>
        <button className="btn btn-ghost text-sm">↻ Refresh</button>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {services.map(({ key, label }) => (
          <div 
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.75rem',
              background: 'var(--bg-tertiary)',
              borderRadius: 8,
            }}
          >
            <span>{label}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {getStatusIcon(health[key])}
              <span className="text-sm">{getStatusLabel(health[key])}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [staff, setStaff] = useState<StaffMember[]>(mockStaff);
  const [roleRequests, setRoleRequests] = useState<RoleRequest[]>(mockRoleRequests);

  const handleDeactivate = (id: string) => {
    setStaff(prev => prev.map(s => 
      s.id === id 
        ? { ...s, status: s.status === 'active' ? 'inactive' : 'active' }
        : s
    ));
  };

  const handleChangeRole = (id: string, newRole: string) => {
    setStaff(prev => prev.map(s => 
      s.id === id ? { ...s, role: newRole } : s
    ));
  };

  const handleApproveRequest = (id: string) => {
    const request = roleRequests.find(r => r.id === id);
    if (request) {
      // Update staff role
      setStaff(prev => prev.map(s => 
        s.staff_id === request.staff_id ? { ...s, role: request.requested_role } : s
      ));
    }
    setRoleRequests(prev => prev.filter(r => r.id !== id));
  };

  const handleRejectRequest = (id: string) => {
    setRoleRequests(prev => prev.filter(r => r.id !== id));
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Admin Dashboard</h1>
        <p className="text-muted">Manage staff, roles, and system configuration</p>
      </div>

      <StatsRow />

      <div style={{ marginTop: '1.5rem' }}>
        <StaffTable 
          staff={staff}
          onDeactivate={handleDeactivate}
          onChangeRole={handleChangeRole}
        />
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        <RoleRequestsQueue 
          requests={roleRequests}
          onApprove={handleApproveRequest}
          onReject={handleRejectRequest}
        />
        <SystemHealthPanel />
      </div>
    </div>
  );
}
