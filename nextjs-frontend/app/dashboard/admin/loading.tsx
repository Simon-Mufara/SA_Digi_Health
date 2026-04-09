export default function AdminLoading() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="skeleton" style={{ width: 180, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 300, height: 16 }} />
      </div>

      {/* Stats skeleton */}
      <div className="stats-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="stat-card">
            <div className="skeleton" style={{ width: 80, height: 12, marginBottom: 8 }} />
            <div className="skeleton" style={{ width: 50, height: 32 }} />
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div className="skeleton" style={{ width: 160, height: 20 }} />
        </div>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} style={{ display: 'flex', gap: '1rem', padding: '0.75rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="skeleton" style={{ width: 80, height: 16 }} />
            <div className="skeleton" style={{ width: 150, height: 16, flex: 1 }} />
            <div className="skeleton" style={{ width: 80, height: 24 }} />
            <div className="skeleton" style={{ width: 60, height: 24 }} />
          </div>
        ))}
      </div>
    </div>
  );
}
