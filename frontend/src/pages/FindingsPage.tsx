import { useNavigate } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { useFindings } from '../hooks/useFindings';

const severityBadge: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-blue-100 text-blue-700 border-blue-200',
  info: 'bg-slate-100 text-slate-700 border-slate-200',
};

const statusBadge: Record<string, string> = {
  open: 'bg-slate-100 text-slate-700',
  confirmed: 'bg-orange-100 text-orange-700',
  false_positive: 'bg-green-100 text-green-700',
  remediated: 'bg-green-100 text-green-700',
  accepted_risk: 'bg-purple-100 text-purple-700',
};

export default function FindingsPage() {
  const navigate = useNavigate();
  const { selectedProject } = useProject();
  const projectId = selectedProject?.id;
  const { findings, loading, error } = useFindings(projectId);

  const handleExportCSV = () => {
    if (!findings || findings.length === 0) return;
    const csv = [
      ['Title', 'Severity', 'CVSS', 'CVE', 'Status'].join(','),
      ...findings.map((f) =>
        [`"${f.title || ''}"`, f.severity || '', f.cvss_score ?? '', f.cve_id || '', f.status || ''].join(',')
      ),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'findings.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Findings</h1>
          <p className="text-slate-500 mt-1">All vulnerabilities discovered across monitored assets.</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleExportCSV}
            disabled={!findings || findings.length === 0}
            className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Export CSV
          </button>
          <button
            onClick={() => navigate('/scans')}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
          >
            Run Scan
          </button>
        </div>
      </div>

      {!selectedProject && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 rounded-lg px-4 py-3 text-sm">
          No project selected. Create or select a project to see findings.
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
            <tr>
              <th className="px-6 py-4">Title</th>
              <th className="px-6 py-4">Severity</th>
              <th className="px-6 py-4">CVSS</th>
              <th className="px-6 py-4">CVE</th>
              <th className="px-6 py-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={5} className="px-6 py-10 text-center text-slate-400">
                  Loading findings...
                </td>
              </tr>
            )}
            {!loading && (!findings || findings.length === 0) && (
              <tr>
                <td colSpan={5} className="px-6 py-10 text-center text-slate-400">
                  {selectedProject
                    ? 'No findings yet. Run a scan to discover vulnerabilities.'
                    : 'Select a project to see findings.'}
                </td>
              </tr>
            )}
            {!loading && findings && findings.map((finding) => (
              <tr key={finding.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 font-medium text-slate-900 max-w-xs truncate">
                  {finding.title || 'Untitled Finding'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${severityBadge[finding.severity] ?? severityBadge.info}`}>
                    {finding.severity
                      ? finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1)
                      : 'Info'}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-slate-600">
                  {finding.cvss_score != null ? Number(finding.cvss_score).toFixed(1) : '—'}
                </td>
                <td className="px-6 py-4 text-slate-500 font-mono text-xs">
                  {finding.cve_id || '—'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-md font-medium ${statusBadge[finding.status] ?? 'bg-slate-100 text-slate-700'}`}>
                    {finding.status ? finding.status.replace('_', ' ') : 'open'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
