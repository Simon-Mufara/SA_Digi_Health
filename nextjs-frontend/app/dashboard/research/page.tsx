'use client';

import { useState, useEffect, useCallback } from 'react';

interface CohortData {
  age_group: string;
  gender: string;
  diagnosis_category: string;
  visit_count: number;
}

interface DiseaseDistribution {
  disease_group: string;
  count: number;
  percentage: number;
}

interface MonthlyVisit {
  month: string;
  count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

// Mock data for PHDC-aligned analytics
const mockCohorts: CohortData[] = [
  { age_group: '0-4', gender: 'M', diagnosis_category: 'ALRI', visit_count: 12 },
  { age_group: '0-4', gender: 'F', diagnosis_category: 'ALRI', visit_count: 7 },
  { age_group: '5-14', gender: 'M', diagnosis_category: 'Injury', visit_count: 15 },
  { age_group: '5-14', gender: 'F', diagnosis_category: 'Injury', visit_count: 8 },
  { age_group: '15-49', gender: 'M', diagnosis_category: 'HIV', visit_count: 45 },
  { age_group: '15-49', gender: 'F', diagnosis_category: 'Maternal', visit_count: 74 },
  { age_group: '15-49', gender: 'F', diagnosis_category: 'HIV', visit_count: 62 },
  { age_group: '50-64', gender: 'M', diagnosis_category: 'NCD', visit_count: 98 },
  { age_group: '50-64', gender: 'F', diagnosis_category: 'NCD', visit_count: 110 },
  { age_group: '65+', gender: 'M', diagnosis_category: 'NCD', visit_count: 55 },
  { age_group: '65+', gender: 'F', diagnosis_category: 'NCD', visit_count: 65 },
  { age_group: '15-49', gender: 'M', diagnosis_category: 'TB', visit_count: 28 },
  { age_group: '15-49', gender: 'M', diagnosis_category: 'Mental Health', visit_count: 21 },
];

const mockDiseaseDistribution: DiseaseDistribution[] = [
  { disease_group: 'NCD', count: 328, percentage: 31.4 },
  { disease_group: 'HIV', count: 107, percentage: 10.3 },
  { disease_group: 'ALRI', count: 171, percentage: 16.4 },
  { disease_group: 'Maternal', count: 109, percentage: 10.5 },
  { disease_group: 'TB', count: 53, percentage: 5.1 },
  { disease_group: 'Injury', count: 63, percentage: 6.0 },
  { disease_group: 'Mental Health', count: 51, percentage: 4.9 },
  { disease_group: 'Other', count: 161, percentage: 15.4 },
];

const mockMonthlyVisits: MonthlyVisit[] = [
  { month: 'Jan 2024', count: 78 },
  { month: 'Feb 2024', count: 85 },
  { month: 'Mar 2024', count: 92 },
  { month: 'Apr 2024', count: 88 },
  { month: 'May 2024', count: 95 },
  { month: 'Jun 2024', count: 102 },
  { month: 'Jul 2024', count: 110 },
  { month: 'Aug 2024', count: 98 },
  { month: 'Sep 2024', count: 105 },
  { month: 'Oct 2024', count: 115 },
  { month: 'Nov 2024', count: 108 },
  { month: 'Dec 2024', count: 90 },
];

function DeidentifiedBanner() {
  return (
    <div className="banner banner-info" style={{ marginBottom: '1.5rem' }}>
      <span>🔒</span>
      <span>
        <strong>De-identified data only.</strong> This dashboard shows aggregate statistics. 
        No patient names, face images, staff IDs, or raw identifiers are displayed.
      </span>
    </div>
  );
}

function StatsRow() {
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total Visits</div>
        <div className="stat-value">1,043</div>
        <div className="stat-change text-muted">Jan 2023 – Mar 2025</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Unique Patients</div>
        <div className="stat-value">300</div>
        <div className="stat-change text-muted">Across 8 facilities</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Disease Groups</div>
        <div className="stat-value">8</div>
        <div className="stat-change text-muted">ICD-10 coded</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Missing BMI</div>
        <div className="stat-value" style={{ color: 'var(--warning)' }}>16%</div>
        <div className="stat-change text-muted">165 records</div>
      </div>
    </div>
  );
}

function CohortBrowser({ data }: { data: CohortData[] }) {
  const [ageFilter, setAgeFilter] = useState<string>('');
  const [genderFilter, setGenderFilter] = useState<string>('');
  const [diagnosisFilter, setDiagnosisFilter] = useState<string>('');

  const ageGroups = [...new Set(data.map(d => d.age_group))];
  const genders = [...new Set(data.map(d => d.gender))];
  const diagnoses = [...new Set(data.map(d => d.diagnosis_category))];

  const filteredData = data.filter(d => 
    (!ageFilter || d.age_group === ageFilter) &&
    (!genderFilter || d.gender === genderFilter) &&
    (!diagnosisFilter || d.diagnosis_category === diagnosisFilter)
  );

  const totalVisits = filteredData.reduce((sum, d) => sum + d.visit_count, 0);

  return (
    <div className="card">
      <div className="card-header">
        <h3>📊 Cohort Browser</h3>
        <span className="font-mono text-sm text-accent">{totalVisits} visits</span>
      </div>

      <div className="grid-3" style={{ gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <label className="label">Age Group</label>
          <select
            className="select"
            value={ageFilter}
            onChange={(e) => setAgeFilter(e.target.value)}
          >
            <option value="">All ages</option>
            {ageGroups.map(ag => (
              <option key={ag} value={ag}>{ag}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Gender</label>
          <select
            className="select"
            value={genderFilter}
            onChange={(e) => setGenderFilter(e.target.value)}
          >
            <option value="">All genders</option>
            {genders.map(g => (
              <option key={g} value={g}>{g === 'M' ? 'Male' : 'Female'}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Diagnosis</label>
          <select
            className="select"
            value={diagnosisFilter}
            onChange={(e) => setDiagnosisFilter(e.target.value)}
          >
            <option value="">All diagnoses</option>
            {diagnoses.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>Age Group</th>
            <th>Gender</th>
            <th>Diagnosis Category</th>
            <th style={{ textAlign: 'right' }}>Visit Count</th>
          </tr>
        </thead>
        <tbody>
          {filteredData.map((row, i) => (
            <tr key={i}>
              <td>{row.age_group}</td>
              <td>{row.gender === 'M' ? 'Male' : 'Female'}</td>
              <td>{row.diagnosis_category}</td>
              <td className="font-mono" style={{ textAlign: 'right' }}>{row.visit_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DiseaseChart({ data }: { data: DiseaseDistribution[] }) {
  const maxCount = Math.max(...data.map(d => d.count));

  const colors: Record<string, string> = {
    NCD: '#3b82f6',
    HIV: '#ef4444',
    ALRI: '#f59e0b',
    Maternal: '#ec4899',
    TB: '#8b5cf6',
    Injury: '#06b6d4',
    'Mental Health': '#10b981',
    Other: '#6b7280',
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>🏥 Disease Burden Distribution</h3>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {data.map(d => (
          <div key={d.disease_group}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <span style={{ fontWeight: 500 }}>{d.disease_group}</span>
              <span className="font-mono text-sm">
                {d.count} ({d.percentage.toFixed(1)}%)
              </span>
            </div>
            <div style={{
              height: 24,
              background: 'var(--bg-tertiary)',
              borderRadius: 4,
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${(d.count / maxCount) * 100}%`,
                height: '100%',
                background: colors[d.disease_group] || 'var(--accent)',
                borderRadius: 4,
                transition: 'width 0.5s ease',
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MonthlyTrendChart({ data }: { data: MonthlyVisit[] }) {
  const maxCount = Math.max(...data.map(d => d.count));
  const chartHeight = 200;

  return (
    <div className="card">
      <div className="card-header">
        <h3>📈 Monthly Visit Trend</h3>
      </div>

      <div style={{ 
        display: 'flex', 
        alignItems: 'flex-end', 
        gap: '0.5rem',
        height: chartHeight,
        padding: '1rem 0',
      }}>
        {data.map((d, i) => (
          <div
            key={d.month}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span className="font-mono text-xs text-muted">{d.count}</span>
            <div
              style={{
                width: '100%',
                height: `${(d.count / maxCount) * (chartHeight - 60)}px`,
                background: 'linear-gradient(180deg, var(--accent), rgba(0, 180, 160, 0.5))',
                borderRadius: '4px 4px 0 0',
                transition: 'height 0.3s ease',
              }}
            />
            <span className="text-xs text-muted" style={{ 
              writingMode: 'vertical-rl',
              transform: 'rotate(180deg)',
              height: 50,
            }}>
              {d.month.split(' ')[0]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ExportControls() {
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');

  const handleExport = async () => {
    setExporting(true);
    
    try {
      // Try real API first
      const res = await fetch(
        `${API_URL}/api/v1/analytics/cohort-export?format=${exportFormat}`,
        { credentials: 'include' }
      );
      
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cohort-export-deidentified.${exportFormat}`;
        a.click();
      } else {
        // Fallback to mock data
        const mockExport = exportFormat === 'csv'
          ? 'age_group,gender,diagnosis_category,visit_count\n0-4,M,ALRI,12\n0-4,F,ALRI,7'
          : JSON.stringify(mockCohorts, null, 2);
        
        const blob = new Blob([mockExport], { 
          type: exportFormat === 'csv' ? 'text/csv' : 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cohort-export-deidentified.${exportFormat}`;
        a.click();
      }
    } catch {
      // Fallback on error
      const mockExport = 'age_group,gender,diagnosis_category,visit_count\n0-4,M,ALRI,12';
      const blob = new Blob([mockExport], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cohort-export-deidentified.csv';
      a.click();
    }
    
    setExporting(false);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>💾 Export Data</h3>
      </div>
      
      <p className="text-sm text-muted" style={{ marginBottom: '1rem' }}>
        Download de-identified cohort data for external analysis. 
        All personally identifiable information (PII) is automatically removed.
      </p>

      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label className="label">Format</label>
          <select
            className="select"
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json')}
          >
            <option value="csv">CSV (Spreadsheet)</option>
            <option value="json">JSON (Programmatic)</option>
          </select>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleExport}
          disabled={exporting}
        >
          {exporting ? '⏳ Preparing...' : '📥 Export'}
        </button>
      </div>
    </div>
  );
}

function DataQualityAudit() {
  const qualityData = [
    { column: 'gender', nullCount: 37, pctMissing: 3.5, severity: 'low' },
    { column: 'age', nullCount: 0, pctMissing: 0, severity: 'complete' },
    { column: 'bmi', nullCount: 165, pctMissing: 15.8, severity: 'high' },
    { column: 'systolic_bp', nullCount: 165, pctMissing: 15.8, severity: 'high' },
    { column: 'diastolic_bp', nullCount: 165, pctMissing: 15.8, severity: 'high' },
  ];

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'complete': return { color: 'var(--success)', bg: 'rgba(16, 185, 129, 0.1)' };
      case 'low': return { color: 'var(--info)', bg: 'rgba(59, 130, 246, 0.1)' };
      case 'high': return { color: 'var(--warning)', bg: 'rgba(245, 158, 11, 0.1)' };
      default: return { color: 'var(--text-muted)', bg: 'transparent' };
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>🔍 Data Quality Audit</h3>
      </div>
      
      <table className="table">
        <thead>
          <tr>
            <th>Column</th>
            <th style={{ textAlign: 'right' }}>Null Count</th>
            <th style={{ textAlign: 'right' }}>% Missing</th>
            <th>Severity</th>
          </tr>
        </thead>
        <tbody>
          {qualityData.map(row => {
            const style = getSeverityStyle(row.severity);
            return (
              <tr key={row.column}>
                <td className="font-mono">{row.column}</td>
                <td className="font-mono" style={{ textAlign: 'right' }}>{row.nullCount}</td>
                <td className="font-mono" style={{ textAlign: 'right' }}>{row.pctMissing}%</td>
                <td>
                  <span style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: 4,
                    background: style.bg,
                    color: style.color,
                    fontSize: '0.75rem',
                    fontWeight: 500,
                  }}>
                    {row.severity}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function ResearchDashboard() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Research Analytics</h1>
        <p className="text-muted">PHDC-aligned health analytics and cohort analysis</p>
      </div>

      <DeidentifiedBanner />
      
      <StatsRow />

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        <DiseaseChart data={mockDiseaseDistribution} />
        <MonthlyTrendChart data={mockMonthlyVisits} />
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <CohortBrowser data={mockCohorts} />
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        <DataQualityAudit />
        <ExportControls />
      </div>
    </div>
  );
}
