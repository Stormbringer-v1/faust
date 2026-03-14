import type { FC } from 'react';

export const RiskTrendChart: FC = () => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 lg:col-span-2 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-slate-800 text-xl font-semibold">Risk Score Trend</h3>
        <span className="text-slate-500 text-xs">Last 30 Days</span>
      </div>
      {/* Chart Placeholder */}
      <div className="flex-1 min-h-[240px] relative w-full flex items-end">
        {/* Simulated Line Chart via CSS gradient/SVG path concept */}
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,var(--color-brand-100)_0%,transparent_100%)] rounded-b-lg [clip-path:polygon(0_60%,20%_50%,40%_70%,60%_30%,80%_40%,100%_20%,100%_100%,0_100%)]"></div>
        {/* Grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between border-t border-b border-slate-100 border-opacity-50">
          <div className="w-full h-px bg-slate-100 opacity-50"></div>
          <div className="w-full h-px bg-slate-100 opacity-50"></div>
          <div className="w-full h-px bg-slate-100 opacity-50"></div>
        </div>
        {/* The Line */}
        <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
          <path d="M0,60 L20,50 L40,70 L60,30 L80,40 L100,20" fill="none" stroke="var(--color-brand-600)" strokeLinejoin="round" strokeWidth="2" vectorEffect="non-scaling-stroke"></path>
        </svg>
      </div>
      {/* X-Axis Labels */}
      <div className="flex justify-between text-slate-400 text-[10px] mt-4 uppercase tracking-wider">
        <span>Oct 1</span>
        <span>Oct 8</span>
        <span>Oct 15</span>
        <span>Oct 22</span>
        <span>Oct 30</span>
      </div>
    </div>
  );
};
