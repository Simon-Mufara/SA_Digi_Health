const steps = [
  {
    title: 'Patient Arrives',
    desc: 'Patient approaches registration kiosk',
  },
  {
    title: 'Face Capture',
    desc: 'YOLOv8 detects face and checks liveness',
  },
  {
    title: 'Matching',
    desc: 'ArcFace compares with patient database',
  },
  {
    title: 'Patient Found',
    desc: 'Patient verified and record retrieved',
  },
  {
    title: 'Care Continues',
    desc: 'Nurse accesses full medical history and starts consult',
  },
];

export default function ProcessSteps() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mt-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {steps.map((step, idx) => (
          <div key={idx} className="rounded-lg border border-slate-200 p-3">
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold mb-2 text-xs">{idx + 1}</div>
            <div className="font-semibold text-sm mb-1 text-slate-800">{step.title}</div>
            <div className="text-xs text-slate-500">{step.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

