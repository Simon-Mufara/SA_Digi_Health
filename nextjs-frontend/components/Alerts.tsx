const alerts = [
  { type: 'warning', text: '2 Duplicate Records Detected' },
  { type: 'danger', text: '1 High Risk (Possible Fraud)' },
  { type: 'info', text: 'System Update Available' },
];

const alertColors = {
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
};

export default function Alerts() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <h3 className="font-semibold mb-3 text-slate-800">Alerts</h3>
      <ul className="space-y-2">
        {alerts.map((a, i) => (
          <li key={i} className={`px-3 py-2 rounded-md text-sm ${(alertColors as Record<string, string>)[a.type]}`}>{a.text}</li>
        ))}
      </ul>
    </div>
  );
}

