const statuses = [
  { label: 'YOLOv8 Detector', status: 'Online' },
  { label: 'Face Recognizer', status: 'Online' },
  { label: 'HPRS Connection', status: 'Online' },
  { label: 'Database', status: 'Online' },
  { label: 'YARA Security', status: 'Active' },
];

export default function SystemStatus() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <h3 className="font-semibold mb-3 text-slate-800">System Status</h3>
      <ul className="space-y-2">
        {statuses.map((s, i) => (
          <li key={i} className="flex items-center justify-between text-sm">
            <span className="text-slate-600">{s.label}</span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${s.status === 'Online' || s.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{s.status}</span>
          </li>
        ))}
      </ul>
      <div className="text-xs text-slate-400 mt-3">Last Sync: 10:42 AM</div>
    </div>
  );
}

