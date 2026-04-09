export default function DemoVideo() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="bg-[#0b2342] text-white rounded-xl p-4 min-h-[210px] flex flex-col justify-between">
        <div>
          <h3 className="font-bold text-lg">PROTOTYPE DEMO VIDEO</h3>
          <p className="text-sm text-blue-100/80">(concept walkthrough)</p>
        </div>
        <div className="text-xs text-blue-100/70">0:00 / 1:12</div>
      </div>
      <div className="lg:col-span-2 rounded-xl bg-slate-200 min-h-[210px] border border-slate-300 flex items-end p-4">
        <span className="text-xs bg-black/60 text-white px-2 py-1 rounded">Secure. Fast. Accurate. Built for South Africa.</span>
      </div>
    </div>
  );
}
