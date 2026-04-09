export default function Activity() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <h3 className="font-semibold mb-3 text-slate-800">Today's Activity</h3>
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between"><span className="text-slate-600">Patients Identified</span><span className="font-semibold">124</span></div>
        <div className="flex items-center justify-between"><span className="text-slate-600">New Registrations</span><span className="font-semibold">18</span></div>
        <div className="flex items-center justify-between"><span className="text-slate-600">Appointments</span><span className="font-semibold">32</span></div>
        <div className="flex items-center justify-between"><span className="text-slate-600">Average Match Score</span><span className="font-semibold text-emerald-600">0.91</span></div>
      </div>
    </div>
  );
}
