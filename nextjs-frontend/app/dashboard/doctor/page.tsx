'use client';

import { useState, useEffect, useCallback } from 'react';

interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  status: 'waiting' | 'in-progress' | 'complete';
  visitReason: string;
  checkInTime: string;
  faceImage?: string;
}

interface PatientDetail extends Patient {
  identifier?: string;
  visits: Visit[];
}

interface Visit {
  id: string;
  date: string;
  reason: string;
  diagnosis?: string;
  notes?: string;
}

interface AISummary {
  summary: string;
  generated_at: string;
  model_version: string;
  is_cached: boolean;
  is_fallback: boolean;
}

// Mock data for demo
const mockPatients: Patient[] = [
  { id: '1', name: 'Thabo Molefe', age: 45, gender: 'M', status: 'waiting', visitReason: 'Follow-up NCD', checkInTime: '08:30' },
  { id: '2', name: 'Naledi Khumalo', age: 32, gender: 'F', status: 'in-progress', visitReason: 'HIV Review', checkInTime: '09:15' },
  { id: '3', name: 'Johannes van der Berg', age: 58, gender: 'M', status: 'waiting', visitReason: 'Chest pain', checkInTime: '09:45' },
  { id: '4', name: 'Precious Dlamini', age: 28, gender: 'F', status: 'complete', visitReason: 'Antenatal', checkInTime: '08:00' },
  { id: '5', name: 'Ahmed Patel', age: 67, gender: 'M', status: 'waiting', visitReason: 'Diabetes check', checkInTime: '10:00' },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

function StatsRow() {
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Today's Patients</div>
        <div className="stat-value">{mockPatients.length}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Waiting</div>
        <div className="stat-value" style={{ color: 'var(--warning)' }}>
          {mockPatients.filter(p => p.status === 'waiting').length}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">In Progress</div>
        <div className="stat-value" style={{ color: 'var(--info)' }}>
          {mockPatients.filter(p => p.status === 'in-progress').length}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Completed</div>
        <div className="stat-value" style={{ color: 'var(--success)' }}>
          {mockPatients.filter(p => p.status === 'complete').length}
        </div>
      </div>
    </div>
  );
}

function PatientSearch({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState('');
  
  return (
    <div style={{ display: 'flex', gap: '0.75rem', margin: '1.5rem 0' }}>
      <input
        type="text"
        className="input"
        placeholder="Search by name, ID, or use face recognition..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch(query)}
        style={{ flex: 1 }}
      />
      <button className="btn btn-primary" onClick={() => onSearch(query)}>
        🔍 Search
      </button>
      <button className="btn btn-secondary">
        📷 Face Search
      </button>
    </div>
  );
}

function PatientList({ 
  patients, 
  onSelectPatient 
}: { 
  patients: Patient[]; 
  onSelectPatient: (p: Patient) => void;
}) {
  const getStatusChip = (status: Patient['status']) => {
    const classes: Record<string, string> = {
      'waiting': 'chip chip-waiting',
      'in-progress': 'chip chip-in-progress',
      'complete': 'chip chip-complete',
    };
    const labels: Record<string, string> = {
      'waiting': 'Waiting',
      'in-progress': 'In Progress',
      'complete': 'Complete',
    };
    return <span className={classes[status]}>{labels[status]}</span>;
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>Today's Patients</h3>
        <span className="text-muted text-sm">{patients.length} patients</span>
      </div>
      
      {patients.map(patient => (
        <div
          key={patient.id}
          onClick={() => onSelectPatient(patient)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            padding: '0.875rem 0',
            borderBottom: '1px solid var(--border-subtle)',
            cursor: 'pointer',
            transition: 'background 0.15s',
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'var(--bg-tertiary)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
        >
          {/* Avatar placeholder */}
          <div style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            color: 'var(--text-muted)',
          }}>
            {patient.gender === 'M' ? '👨' : '👩'}
          </div>
          
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
              {patient.name}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {patient.age}y · {patient.gender} · {patient.visitReason}
            </div>
          </div>
          
          <div style={{ textAlign: 'right' }}>
            {getStatusChip(patient.status)}
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {patient.checkInTime}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function AISummaryCard({
  patientId,
  patientName,
  patientAge,
  patientGender,
  visitReason,
}: {
  patientId: string;
  patientName: string;
  patientAge: number;
  patientGender: string;
  visitReason: string;
}) {
  const [summary, setSummary] = useState<AISummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async (force: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/ai/summarise/${patientId}${force ? '?force=true' : ''}`,
        { credentials: 'include' }
      );
      if (res.ok) {
        const data: AISummary = await res.json();
        setSummary(data);
      } else {
        throw new Error('Failed to fetch');
      }
    } catch {
      // Fallback summary for demo
      setSummary({
        summary: `SUMMARY: ${patientGender === 'M' ? 'Male' : 'Female'} patient, ${patientAge} years old, presenting for ${visitReason.toLowerCase()}. Review of systems and current medications recommended.\n\nFLAGS: None\n\nTREND: insufficient data`,
        generated_at: new Date().toISOString(),
        model_version: 'demo-fallback',
        is_cached: false,
        is_fallback: true,
      });
    }
    setLoading(false);
  }, [patientId, patientName, patientAge, patientGender, visitReason]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Parse structured summary
  const parseSummary = (text: string) => {
    const sections: { summary: string; flags: string; trend: string } = {
      summary: '',
      flags: '',
      trend: '',
    };
    
    const summaryMatch = text.match(/SUMMARY:\s*([\s\S]*?)(?=FLAGS:|TREND:|$)/i);
    const flagsMatch = text.match(/FLAGS:\s*([\s\S]*?)(?=TREND:|$)/i);
    const trendMatch = text.match(/TREND:\s*([\s\S]*?)$/i);
    
    if (summaryMatch) sections.summary = summaryMatch[1].trim();
    if (flagsMatch) sections.flags = flagsMatch[1].trim();
    if (trendMatch) sections.trend = trendMatch[1].trim();
    
    // If no structured format, use the whole text as summary
    if (!sections.summary && !sections.flags && !sections.trend) {
      sections.summary = text;
    }
    
    return sections;
  };

  const formatTimestamp = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleString('en-ZA', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTrendColor = (trend: string) => {
    const lower = trend.toLowerCase();
    if (lower.includes('improving')) return 'var(--success)';
    if (lower.includes('concerning')) return 'var(--error)';
    if (lower.includes('stable')) return 'var(--info)';
    return 'var(--text-muted)';
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-header">
          <h4>🤖 AI Clinical Summary</h4>
        </div>
        <div style={{ padding: '1rem' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.75rem',
            color: 'var(--primary)',
            marginBottom: '1rem',
          }}>
            <div className="loading-spinner" style={{ width: 20, height: 20 }} />
            <span style={{ fontStyle: 'italic' }}>Analysing patient history...</span>
          </div>
          <div className="skeleton" style={{ height: 16, marginBottom: 8, width: '100%' }} />
          <div className="skeleton" style={{ height: 16, marginBottom: 8, width: '90%' }} />
          <div className="skeleton" style={{ height: 16, width: '75%' }} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--error)' }}>
        <div className="card-header">
          <h4>🤖 AI Clinical Summary</h4>
          <button className="btn btn-ghost text-sm" onClick={() => fetchSummary(true)}>
            ↻ Retry
          </button>
        </div>
        <div style={{ 
          padding: '1rem', 
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '0.5rem',
          color: 'var(--error)',
        }}>
          ⚠️ AI summary unavailable — please review records manually
        </div>
      </div>
    );
  }

  const parsed = summary ? parseSummary(summary.summary) : null;

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h4>🤖 AI Clinical Summary</h4>
          {summary?.is_fallback && (
            <span className="chip" style={{ 
              background: 'var(--warning)', 
              color: '#000',
              fontSize: '0.65rem',
              padding: '0.15rem 0.4rem',
            }}>
              FALLBACK
            </span>
          )}
          {summary?.is_cached && (
            <span className="chip" style={{ 
              background: 'var(--bg-tertiary)', 
              fontSize: '0.65rem',
              padding: '0.15rem 0.4rem',
            }}>
              CACHED
            </span>
          )}
        </div>
        <button 
          className="btn btn-ghost text-sm"
          onClick={() => fetchSummary(true)}
          title="Regenerate summary"
        >
          ↻ Regenerate
        </button>
      </div>
      
      {parsed && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Summary text */}
          <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
            {parsed.summary}
          </p>
          
          {/* Flags section with monospace */}
          {parsed.flags && (
            <div style={{
              background: parsed.flags.toLowerCase() === 'none' 
                ? 'var(--bg-tertiary)' 
                : 'rgba(239, 68, 68, 0.1)',
              padding: '0.75rem',
              borderRadius: '0.375rem',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
            }}>
              <strong>FLAGS:</strong>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                marginTop: '0.25rem',
                color: parsed.flags.toLowerCase() === 'none' 
                  ? 'var(--text-muted)' 
                  : 'var(--error)',
              }}>
                {parsed.flags}
              </div>
            </div>
          )}
          
          {/* Trend indicator */}
          {parsed.trend && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              fontSize: '0.85rem',
            }}>
              <strong>Trend:</strong>
              <span style={{ 
                color: getTrendColor(parsed.trend),
                fontWeight: 500,
              }}>
                {parsed.trend}
              </span>
            </div>
          )}
          
          {/* Timestamp footer */}
          <div style={{ 
            fontSize: '0.7rem', 
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '0.5rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid var(--border-subtle)',
          }}>
            <span>Generated: {summary ? formatTimestamp(summary.generated_at) : '-'}</span>
            <span>Model: {summary?.model_version || '-'}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function PatientPanel({
  patient,
  onClose,
}: {
  patient: Patient;
  onClose: () => void;
}) {
  const [note, setNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  const mockVisits: Visit[] = [
    { id: 'v1', date: '2025-01-15', reason: 'Follow-up', diagnosis: 'E11 - Type 2 DM', notes: 'HbA1c improved' },
    { id: 'v2', date: '2024-10-20', reason: 'Routine check', diagnosis: 'I10 - Hypertension', notes: 'BP controlled' },
    { id: 'v3', date: '2024-07-05', reason: 'Acute visit', diagnosis: 'J06.9 - URTI', notes: 'Symptomatic Rx' },
  ];

  const handleSaveNote = async () => {
    if (!note.trim()) return;
    setSavingNote(true);
    try {
      await fetch(`${API_URL}/api/v1/visits/${patient.id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ content: note }),
      });
      setNote('');
    } catch {
      // Demo mode - just clear
      setNote('');
    }
    setSavingNote(false);
  };

  return (
    <>
      {/* Overlay */}
      <div 
        className="slide-panel-overlay open"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="slide-panel open">
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <div style={{ 
            padding: '1.25rem', 
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'var(--bg-tertiary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.75rem',
              }}>
                {patient.gender === 'M' ? '👨' : '👩'}
              </div>
              <div>
                <h3>{patient.name}</h3>
                <div className="text-muted text-sm">
                  {patient.age} years · {patient.gender === 'M' ? 'Male' : 'Female'}
                </div>
              </div>
            </div>
            <button className="btn btn-ghost" onClick={onClose}>✕</button>
          </div>

          {/* Content */}
          <div style={{ flex: 1, overflow: 'auto', padding: '1.25rem' }}>
            {/* AI Summary */}
            <AISummaryCard
              patientId={patient.id}
              patientName={patient.name}
              patientAge={patient.age}
              patientGender={patient.gender}
              visitReason={patient.visitReason}
            />

            {/* Visit Timeline */}
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div className="card-header">
                <h4>📋 Visit Timeline</h4>
              </div>
              {mockVisits.map((visit, i) => (
                <div 
                  key={visit.id}
                  style={{
                    padding: '0.75rem 0',
                    borderBottom: i < mockVisits.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span className="font-mono text-sm">{visit.date}</span>
                    <span className="text-sm text-muted">{visit.reason}</span>
                  </div>
                  <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                    {visit.diagnosis}
                  </div>
                  <div className="text-sm text-muted">{visit.notes}</div>
                </div>
              ))}
            </div>

            {/* Quick Note */}
            <div className="card">
              <div className="card-header">
                <h4>📝 Quick Note</h4>
              </div>
              <textarea
                className="textarea"
                placeholder="Add a clinical note for this visit..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                style={{ minHeight: 100, marginBottom: '0.75rem' }}
              />
              <button 
                className="btn btn-primary" 
                disabled={!note.trim() || savingNote}
                onClick={handleSaveNote}
              >
                {savingNote ? 'Saving...' : 'Save Note'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function DoctorDashboard() {
  const [patients, setPatients] = useState<Patient[]>(mockPatients);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setPatients(mockPatients);
      return;
    }
    const filtered = mockPatients.filter(p => 
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.visitReason.toLowerCase().includes(query.toLowerCase())
    );
    setPatients(filtered);
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Doctor Dashboard</h1>
        <p className="text-muted">Manage your patients and clinical workflows</p>
      </div>

      <StatsRow />
      
      <PatientSearch onSearch={handleSearch} />
      
      <PatientList 
        patients={patients} 
        onSelectPatient={setSelectedPatient}
      />

      {selectedPatient && (
        <PatientPanel
          patient={selectedPatient}
          onClose={() => setSelectedPatient(null)}
        />
      )}
    </div>
  );
}
