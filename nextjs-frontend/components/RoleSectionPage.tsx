interface RoleSectionPageProps {
  title: string;
  subtitle: string;
  tag: string;
  backHref: string;
  highlights: string[];
  checklist: string[];
}

export default function RoleSectionPage({
  title,
  subtitle,
  tag,
  backHref,
  highlights,
  checklist,
}: RoleSectionPageProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <h1 style={{ marginBottom: '0.35rem' }}>{title}</h1>
            <p className="text-muted">{subtitle}</p>
          </div>
          <span className="chip chip-in-progress">{tag}</span>
        </div>

        <div className="grid-2" style={{ alignItems: 'start' }}>
          <div>
            <h4 style={{ marginBottom: '0.5rem' }}>Priority focus</h4>
            <ul style={{ display: 'grid', gap: '0.5rem', paddingLeft: '1.1rem' }}>
              {highlights.map((item) => (
                <li key={item} className="text-secondary">{item}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4 style={{ marginBottom: '0.5rem' }}>Shift checklist</h4>
            <ul style={{ display: 'grid', gap: '0.45rem' }}>
              {checklist.map((item) => (
                <li key={item} className="card" style={{ padding: '0.65rem 0.8rem', borderRadius: 8 }}>
                  <span className="text-sm">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="text-sm" style={{ fontWeight: 600 }}>South African DigiHealth</div>
          <div className="text-xs text-muted">Presentation-ready operational view for clinics and hospitals.</div>
        </div>
        <a href={backHref} className="btn btn-secondary">Back to overview</a>
      </div>
    </div>
  );
}
