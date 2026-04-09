export default function ResearchLoading() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 300, height: 16 }} />
      </div>

      {/* De-identified banner skeleton */}
      <div className="skeleton" style={{ height: 50, marginBottom: '1.5rem', borderRadius: 8 }} />

      {/* Stats skeleton */}
      <div className="stats-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="stat-card">
            <div className="skeleton" style={{ width: 100, height: 12, marginBottom: 8 }} />
            <div className="skeleton" style={{ width: 60, height: 32 }} />
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem', alignItems: 'start' }}>
        {/* Disease chart skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 200, height: 20 }} />
          </div>
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} style={{ marginBottom: '0.75rem' }}>
              <div className="skeleton" style={{ width: 80, height: 14, marginBottom: 4 }} />
              <div className="skeleton" style={{ height: 24, borderRadius: 4 }} />
            </div>
          ))}
        </div>

        {/* Monthly trend skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 180, height: 20 }} />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', height: 200, alignItems: 'flex-end' }}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(i => (
              <div key={i} className="skeleton" style={{ 
                flex: 1, 
                height: `${30 + Math.random() * 60}%`,
                borderRadius: '4px 4px 0 0',
              }} />
            ))}
          </div>
        </div>
      </div>

      {/* Cohort browser skeleton */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div className="skeleton" style={{ width: 140, height: 20 }} />
        </div>
        <div className="grid-3" style={{ gap: '1rem', marginBottom: '1rem' }}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 40 }} />
          ))}
        </div>
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} style={{ display: 'flex', gap: '1rem', padding: '0.75rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="skeleton" style={{ width: 60, height: 16 }} />
            <div className="skeleton" style={{ width: 60, height: 16 }} />
            <div className="skeleton" style={{ width: 100, height: 16, flex: 1 }} />
            <div className="skeleton" style={{ width: 50, height: 16 }} />
          </div>
        ))}
      </div>
    </div>
  );
}
