import { Suspense } from 'react';

// Loading skeleton for stats
function StatsSkeleton() {
  return (
    <div className="stats-grid">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="stat-card">
          <div className="skeleton" style={{ width: 80, height: 12, marginBottom: 8 }} />
          <div className="skeleton" style={{ width: 60, height: 32 }} />
        </div>
      ))}
    </div>
  );
}

// Loading skeleton for patient list
function PatientListSkeleton() {
  return (
    <div className="card">
      <div className="card-header">
        <div className="skeleton" style={{ width: 150, height: 20 }} />
      </div>
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%' }} />
          <div style={{ flex: 1 }}>
            <div className="skeleton" style={{ width: '60%', height: 14, marginBottom: 6 }} />
            <div className="skeleton" style={{ width: '40%', height: 12 }} />
          </div>
          <div className="skeleton" style={{ width: 70, height: 24, borderRadius: 12 }} />
        </div>
      ))}
    </div>
  );
}

export default function DoctorLoadingPage() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 300, height: 16 }} />
      </div>

      {/* Stats loading */}
      <Suspense fallback={<StatsSkeleton />}>
        <StatsSkeleton />
      </Suspense>

      {/* Search bar skeleton */}
      <div style={{ margin: '1.5rem 0' }}>
        <div className="skeleton" style={{ width: '100%', height: 44, borderRadius: 8 }} />
      </div>

      {/* Patient list loading */}
      <PatientListSkeleton />
    </div>
  );
}
