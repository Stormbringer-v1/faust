import { useMemo } from 'react';
import { SeverityDonut } from '../components/dashboard/SeverityDonut';
import { RiskTrendChart } from '../components/dashboard/RiskTrendChart';
import { TopAssetsTable } from '../components/dashboard/TopAssetsTable';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { useProject } from '../contexts/ProjectContext';
import { useFindings } from '../hooks/useFindings';
import { useAssets } from '../hooks/useAssets';

export default function DashboardPage() {
  const { selectedProject } = useProject();
  const defaultProjectId = selectedProject?.id;
  
  const { findings, loading: findingsLoading } = useFindings(defaultProjectId);
  const { assets, loading: assetsLoading } = useAssets(defaultProjectId);

  const stats = useMemo(() => {
    const defaultStats = { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 };
    if (!findings) return defaultStats;

    return findings.reduce((acc, f) => {
      acc[f.severity as keyof typeof acc] = (acc[f.severity as keyof typeof acc] || 0) + 1;
      acc.total += 1;
      return acc;
    }, defaultStats);
  }, [findings]);

  // Very simple average risk score calculation (could be more complex)
  const averageRiskScore = useMemo(() => {
    if (!findings || findings.length === 0) return 0;
    const totalScore = findings.reduce((acc, f) => acc + (f.risk_score || 0), 0);
    return Math.round(totalScore / findings.length);
  }, [findings]);

  return (
    <>
      {/* Dashboard Header & Quick Actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <h2 className="text-[3.5rem] leading-none font-bold text-slate-800 tracking-[-0.02em] font-headline">Dashboard</h2>
          <p className="text-slate-500 text-base mt-2">Overview of your security posture</p>
        </div>
        <div className="flex gap-3">
          <button className="bg-brand-600 text-white font-bold text-sm px-6 h-10 rounded-md hover:opacity-90 transition-opacity flex items-center gap-2">
            New Scan
          </button>
          <button className="bg-white border border-slate-200 text-slate-700 font-medium text-sm px-6 h-10 rounded-md hover:bg-slate-50 transition-colors">
            View Findings
          </button>
        </div>
      </div>

      {/* Top Stats Row (Risk Score & Donut) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        {/* Risk Score Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 relative overflow-hidden flex flex-col justify-center">
          <span className="text-slate-500 text-sm font-medium uppercase tracking-wider mb-2 z-10 relative">Average Risk Score</span>
          <div className="flex items-baseline gap-4 z-10 relative">
            <span className="text-[4rem] leading-none font-bold text-slate-800 tracking-tighter">
              {findingsLoading ? '...' : averageRiskScore}
            </span>
          </div>
          <p className="text-slate-500 text-xs mt-4 z-10 relative">Based on {assets?.length || 0} active assets.</p>
        </div>
        
        {/* Vulnerability Severity Donut Area */}
        <SeverityDonut stats={stats} />
      </div>

      {/* Charts & Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <RiskTrendChart />
        <RecentActivity />
      </div>

      {/* Top Assets Row */}
      <div className="mt-8">
        <TopAssetsTable assets={assets} loading={assetsLoading} />
      </div>
    </>
  );
}
