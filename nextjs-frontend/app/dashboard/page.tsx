import Sidebar from '@/components/Sidebar';
import CameraFeed from '@/components/CameraFeed';
import PatientMatch from '@/components/PatientMatch';
import SystemStatus from '@/components/SystemStatus';
import QuickActions from '@/components/QuickActions';
import Activity from '@/components/Activity';
import Alerts from '@/components/Alerts';
import ProcessSteps from '@/components/ProcessSteps';
import DemoVideo from '@/components/DemoVideo';

export default function Dashboard() {
  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar />
      <main className="flex-1 p-4 md:p-6 space-y-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-4 py-3 flex items-center justify-between">
          <div className="text-sm text-slate-700"><span className="font-semibold">Dashboard</span> • Live Identification</div>
          <div className="text-xs text-slate-500">Secure Connection</div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <CameraFeed />
          <PatientMatch />
          <SystemStatus />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <QuickActions />
          <Activity />
          <Alerts />
        </div>
        <ProcessSteps />
        <DemoVideo />
      </main>
    </div>
  );
}
