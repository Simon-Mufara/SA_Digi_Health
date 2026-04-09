export default function QuickActions() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <h3 className="font-semibold mb-3 text-slate-800">Quick Actions</h3>
      <div className="flex flex-col gap-2">
        <button className="w-full px-4 py-2 bg-blue-50 text-blue-700 rounded-md border border-blue-100 text-sm font-medium hover:bg-blue-100">Register New Patient</button>
        <button className="w-full px-4 py-2 bg-blue-50 text-blue-700 rounded-md border border-blue-100 text-sm font-medium hover:bg-blue-100">Capture Biometrics</button>
        <button className="w-full px-4 py-2 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-100 text-sm font-medium hover:bg-emerald-100">Search Patient</button>
      </div>
    </div>
  );
}

