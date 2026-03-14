import { useMemo, useState } from 'react';
import api from '../services/api';
import { useProject } from '../contexts/ProjectContext';
import { useScans } from '../hooks/useScans';

const scanTypes = [
  { value: 'network', label: 'Network', description: 'Nmap host and port discovery.' },
  { value: 'web_app', label: 'Web App', description: 'Nuclei templates and web checks.' },
  { value: 'container', label: 'Container', description: 'Trivy image vulnerability scan.' },
  { value: 'cloud', label: 'Cloud', description: 'Trivy cloud misconfiguration scan.' },
  { value: 'full', label: 'Full', description: 'Run all applicable scanners.' },
];

const profiles = [
  { value: 'quick', label: 'Quick' },
  { value: 'standard', label: 'Standard' },
  { value: 'thorough', label: 'Thorough' },
  { value: 'stealth', label: 'Stealth' },
];

const statusBadge: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  running: 'bg-blue-100 text-blue-700 border-blue-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  failed: 'bg-red-100 text-red-700 border-red-200',
  cancelled: 'bg-slate-100 text-slate-700 border-slate-200',
};

export default function ScansPage() {
  const { selectedProject } = useProject();
  const projectId = selectedProject?.id;
  const { scans, loading: scansLoading, error: scansError, refresh } = useScans(projectId);

  const [scanType, setScanType] = useState('network');
  const [profile, setProfile] = useState('standard');
  const [targetsText, setTargetsText] = useState('');
  const [ports, setPorts] = useState('21-23, 80, 443, 3389, 8080');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const targets = useMemo(() => {
    return targetsText
      .split(/[\n,]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }, [targetsText]);

  const handleSubmit = async () => {
    if (!projectId) {
      setError('No project available. Create a project first.');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const scannerConfig: Record<string, string> = {};
      if (profile) scannerConfig.profile = profile;
      if (ports) scannerConfig.ports = ports;

      await api.post(`/projects/${projectId}/scans/`, {
        scan_type: scanType,
        targets: targets.length > 0 ? targets : null,
        scanner_config: Object.keys(scannerConfig).length ? scannerConfig : null,
      });
      setSuccess('Scan queued successfully.');
      await refresh();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">New Scan Configuration</h1>
          <p className="text-slate-500 mt-1">Configure targets and launch a security scan.</p>
        </div>
      </div>

      {(error || success) && (
        <div className={`rounded-lg border px-4 py-3 text-sm ${error ? 'border-red-200 bg-red-50 text-red-700' : 'border-green-200 bg-green-50 text-green-700'}`}>
          {error || success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-slate-900">Target Information</h2>
            <p className="text-sm text-slate-500 mt-1">Enter one or more targets separated by commas or new lines.</p>
            <textarea
              className="mt-4 w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              rows={4}
              value={targetsText}
              onChange={(event) => setTargetsText(event.target.value)}
              placeholder="192.168.1.1, 10.0.0.0/24, api.internal.cloud"
            />
            <p className="text-xs text-slate-400 mt-2">Targets must be within the project allowlist.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-slate-900">Scan Type</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              {scanTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setScanType(type.value)}
                  className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                    scanType === type.value
                      ? 'border-brand-500 bg-brand-50'
                      : 'border-slate-200 hover:border-brand-200'
                  }`}
                >
                  <p className="text-sm font-semibold text-slate-900">{type.label}</p>
                  <p className="text-xs text-slate-500 mt-1">{type.description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-slate-900">Scan Profile</h2>
            <div className="flex flex-wrap gap-3 mt-4">
              {profiles.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setProfile(option.value)}
                  className={`px-4 py-2 rounded-full text-xs font-semibold border transition-colors ${
                    profile === option.value
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-slate-200 text-slate-600 hover:border-brand-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-900">Port Range (Network scans)</h3>
            <input
              type="text"
              value={ports}
              onChange={(event) => setPorts(event.target.value)}
              className="mt-3 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            <p className="text-xs text-slate-400 mt-2">Applied to network scan profiles.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-900">Scheduling</h3>
            <p className="text-xs text-slate-500 mt-2">Scheduling is coming soon.</p>
            <div className="mt-4 flex items-center gap-3 text-slate-400 text-xs">
              <span className="px-2 py-1 rounded-full border border-dashed border-slate-300">Run Once</span>
              <span className="px-2 py-1 rounded-full border border-dashed border-slate-300">Daily</span>
              <span className="px-2 py-1 rounded-full border border-dashed border-slate-300">Weekly</span>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
            <p className="text-xs text-slate-500 mt-2">Notifications will be supported in Phase 3.</p>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
          onClick={() => setTargetsText('')}
        >
          Clear Targets
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting}
          className="px-6 py-2 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? 'Starting...' : 'Start Scan'}
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700">Recent Scans</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
            <tr>
              <th className="px-6 py-4">Scan Type</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Findings</th>
              <th className="px-6 py-4">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {scansLoading && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={4}>
                  Loading scans...
                </td>
              </tr>
            )}
            {scansError && !scansLoading && (
              <tr>
                <td className="px-6 py-6 text-red-600" colSpan={4}>
                  {scansError}
                </td>
              </tr>
            )}
            {!scansLoading && scans?.length === 0 && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={4}>
                  No scans found.
                </td>
              </tr>
            )}
            {!scansLoading && scans?.map((scan) => (
              <tr key={scan.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 font-medium text-slate-900 capitalize">{scan.scan_type.replace('_', ' ')}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${statusBadge[scan.status] || statusBadge.pending}`}>
                    {scan.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-600">{scan.finding_count}</td>
                <td className="px-6 py-4 text-slate-600">{new Date(scan.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
