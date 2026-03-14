import type { FC } from 'react';

interface SeverityStats {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}

interface Props {
  stats?: SeverityStats;
}

export const SeverityDonut: FC<Props> = ({ stats }) => {
  const data = stats || { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 };
  
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 lg:col-span-2 flex items-center gap-8">
      <div className="flex-1">
        <h3 className="text-slate-800 text-xl font-semibold mb-6">Active Vulnerabilities</h3>
        <div className="flex gap-8">
          {/* Simulated Donut Chart Space */}
          <div className="relative w-32 h-32 shrink-0 rounded-full border-[16px] border-slate-100 flex items-center justify-center">
            {/* Abstract CSS rings for donut look - simplified for dynamic data in real app */}
            <div className="absolute inset-[-16px] rounded-full border-[16px] border-red-600" style={{ clipPath: data.critical > 0 ? 'polygon(50% 50%, 100% 0, 100% 100%, 50% 100%)' : 'none', opacity: data.critical > 0 ? 1 : 0 }}></div>
            <div className="absolute inset-[-16px] rounded-full border-[16px] border-orange-500" style={{ clipPath: data.high > 0 ? 'polygon(50% 50%, 50% 100%, 0 100%, 0 50%)' : 'none', opacity: data.high > 0 ? 1 : 0 }}></div>
            <div className="absolute inset-[-16px] rounded-full border-[16px] border-yellow-400" style={{ clipPath: data.medium > 0 ? 'polygon(50% 50%, 0 50%, 0 0, 50% 0)' : 'none', opacity: data.medium > 0 ? 1 : 0 }}></div>
            <div className="text-center z-10 relative bg-white w-20 h-20 rounded-full flex flex-col justify-center shadow-sm">
              <span className="block text-2xl font-bold text-slate-800">{data.total}</span>
              <span className="block text-[10px] text-slate-500 uppercase">Total</span>
            </div>
          </div>
          {/* Legend */}
          <div className="flex flex-col justify-center gap-4 flex-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-600"></span>
                <span className="text-sm text-slate-600">Critical</span>
              </div>
              <span className="text-sm font-bold text-slate-800">{data.critical}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-orange-500"></span>
                <span className="text-sm text-slate-600">High</span>
              </div>
              <span className="text-sm font-bold text-slate-800">{data.high}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-400"></span>
                <span className="text-sm text-slate-600">Medium</span>
              </div>
              <span className="text-sm font-bold text-slate-800">{data.medium}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-slate-300"></span>
                <span className="text-sm text-slate-600">Low / Info</span>
              </div>
              <span className="text-sm font-bold text-slate-800">{data.low + data.info}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
