import type { FC } from 'react';

export const RecentActivity: FC = () => {
  return (
    <div className="bg-surface-container rounded-xl p-6 flex flex-col">
      <h3 className="text-on-surface text-xl font-semibold mb-6">Recent Activity</h3>
      <div className="flex-1 flex flex-col gap-6 relative">
        {/* Timeline track */}
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-surface-container-high"></div>
        {/* Item 1 */}
        <div className="flex gap-4 relative z-10">
          <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-0.5">
            <div className="w-2 h-2 rounded-full bg-primary"></div>
          </div>
          <div>
            <p className="text-sm font-medium text-on-surface">External Network Scan Completed</p>
            <p className="text-xs text-on-surface-variant mt-1">Found 12 new vulnerabilities</p>
            <p className="text-[10px] text-outline mt-2">2 hours ago</p>
          </div>
        </div>
        {/* Item 2 */}
        <div className="flex gap-4 relative z-10">
          <div className="w-6 h-6 rounded-full bg-tertiary/20 flex items-center justify-center shrink-0 mt-0.5">
            <div className="w-2 h-2 rounded-full bg-tertiary"></div>
          </div>
          <div>
            <p className="text-sm font-medium text-on-surface">Critical CVE-2023-44487 Detected</p>
            <p className="text-xs text-on-surface-variant mt-1">Impacts 3 edge routers</p>
            <p className="text-[10px] text-outline mt-2">5 hours ago</p>
          </div>
        </div>
        {/* Item 3 */}
        <div className="flex gap-4 relative z-10">
          <div className="w-6 h-6 rounded-full bg-surface-container-high flex items-center justify-center shrink-0 mt-0.5">
            <div className="w-2 h-2 rounded-full bg-on-surface-variant"></div>
          </div>
          <div>
            <p className="text-sm font-medium text-on-surface">Agent Deployment on prod-db-04</p>
            <p className="text-xs text-on-surface-variant mt-1">Status: Successful</p>
            <p className="text-[10px] text-outline mt-2">Yesterday</p>
          </div>
        </div>
      </div>
      <button className="w-full mt-6 py-2 text-sm text-primary hover:bg-primary/5 rounded transition-colors text-center">
        View All Logs
      </button>
    </div>
  );
};
