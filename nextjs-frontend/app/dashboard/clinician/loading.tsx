export default function ClinicianLoading() {
  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 350, height: 16 }} />
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Face capture skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 120, height: 20 }} />
          </div>
          <div className="skeleton" style={{ width: '100%', aspectRatio: '4/3', borderRadius: 8 }} />
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <div className="skeleton" style={{ width: 120, height: 40 }} />
            <div className="skeleton" style={{ width: 120, height: 40 }} />
          </div>
        </div>

        {/* Form skeleton */}
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <div className="skeleton" style={{ width: 140, height: 20 }} />
          </div>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ marginBottom: '1rem' }}>
              <div className="skeleton" style={{ width: 80, height: 12, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: '100%', height: 40 }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
