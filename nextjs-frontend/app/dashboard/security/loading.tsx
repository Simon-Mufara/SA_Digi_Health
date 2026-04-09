export default function SecurityLoading() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 350, height: 16 }} />
      </div>

      {/* Stats skeleton */}
      <div className="stats-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="stat-card">
            <div className="skeleton" style={{ width: 100, height: 12, marginBottom: 8 }} />
            <div className="skeleton" style={{ width: 40, height: 32 }} />
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        {/* Live feed skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 160, height: 20 }} />
          </div>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton" style={{ height: 80, marginBottom: 8, borderRadius: 8 }} />
          ))}
        </div>

        {/* Alerts skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 140, height: 20 }} />
          </div>
          {[1, 2].map(i => (
            <div key={i} className="skeleton" style={{ height: 100, marginBottom: 8, borderRadius: 8 }} />
          ))}
        </div>
      </div>
    </div>
  );
}
