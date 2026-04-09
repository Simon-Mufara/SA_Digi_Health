export default function PatientMatch() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <div className="font-semibold text-slate-800 mb-3">Patient Match</div>
      <div className="flex items-start gap-3">
        <div className="h-14 w-14 rounded-full bg-slate-200" />
        <div className="flex-1">
          <div className="font-semibold text-slate-900">Nomsa Dlamini</div>
          <div className="text-xs text-slate-500">ID: 870101 1234 086</div>
          <div className="text-xs text-slate-500">HPRS ID: 1010 5566 7788 9901</div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-slate-600">Match Score</span>
            <span className="rounded bg-emerald-100 text-emerald-700 px-2 py-0.5 text-xs font-bold">0.93</span>
          </div>
          <div className="text-xs text-emerald-700 font-semibold mt-1">Patient Verified</div>
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-xs font-medium">View Profile</button>
        <button className="flex-1 px-3 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 text-xs font-medium">Open EMR</button>
      </div>
    </div>
  );
}

