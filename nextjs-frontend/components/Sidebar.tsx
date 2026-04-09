export default function Sidebar() {
  return (
    <aside className="w-64 min-h-screen bg-[#06254d] text-white p-4 flex flex-col border-r border-[#154d86]">
      <div className="mb-6">
        <h2 className="text-lg font-bold tracking-tight">SA HealthID</h2>
        <p className="text-[11px] text-blue-100/80">Biometric Patient Identification System</p>
      </div>

      <nav className="flex flex-col gap-2 text-sm">
        <a href="/dashboard" className="rounded-md bg-blue-500/20 px-3 py-2 border border-blue-300/20">Dashboard</a>
        <a href="/dashboard/clinician" className="rounded-md px-3 py-2 hover:bg-blue-500/20">Patient Lookup</a>
        <a href="/dashboard/security" className="rounded-md px-3 py-2 hover:bg-blue-500/20">Registration</a>
        <a href="/dashboard/doctor" className="rounded-md px-3 py-2 hover:bg-blue-500/20">Appointments</a>
        <a href="/dashboard/research" className="rounded-md px-3 py-2 hover:bg-blue-500/20">Reports</a>
        <a href="/dashboard/admin" className="rounded-md px-3 py-2 hover:bg-blue-500/20">System Settings</a>
      </nav>

      <div className="mt-auto pt-6 border-t border-blue-200/20 text-xs text-blue-100/80">
        <div>User: Nurse Thandi</div>
        <div>Facility: Khayelitsha CHC</div>
        <button className="mt-3 w-full rounded-md bg-white/10 py-2 hover:bg-white/20">Logout</button>
      </div>
    </aside>
  );
}
