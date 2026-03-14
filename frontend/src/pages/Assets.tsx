import { useMemo, useState } from 'react';
import api from '../services/api';
import { useProject } from '../contexts/ProjectContext';
import { useAssets } from '../hooks/useAssets';
import { useFindings } from '../hooks/useFindings';

const ASSET_TYPES = ['host', 'domain', 'url', 'cidr', 'cloud_resource'] as const;

function AddAssetModal({ projectId, onClose, onSuccess }: {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState('');
  const [assetType, setAssetType] = useState<string>('host');
  const [identifier, setIdentifier] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) { setError('Identifier is required.'); return; }
    setSubmitting(true);
    setError(null);
    try {
      await api.post(`/projects/${projectId}/assets/`, {
        name: name.trim() || identifier.trim(),
        asset_type: assetType,
        identifier: identifier.trim(),
        description: description.trim() || null,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to create asset.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-slate-900">Add Asset</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Identifier <span className="text-red-500">*</span></label>
            <input
              autoFocus
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="192.168.1.1, api.example.com, etc."
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Asset Type</label>
            <select
              value={assetType}
              onChange={(e) => setAssetType(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30 bg-white"
            >
              {ASSET_TYPES.map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1).replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Name <span className="text-slate-400 font-normal">(optional)</span></label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Defaults to identifier if blank"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description <span className="text-slate-400 font-normal">(optional)</span></label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Brief note about this asset"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Adding...' : 'Add Asset'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const severityRank: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
  info: 0,
};

const severityBadge: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-blue-100 text-blue-700 border-blue-200',
  info: 'bg-slate-100 text-slate-700 border-slate-200',
};

const parseTags = (tags?: string | null): string[] => {
  if (!tags) return [];
  try {
    const parsed = JSON.parse(tags);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export default function AssetsPage() {
  const { selectedProject } = useProject();
  const projectId = selectedProject?.id;
  const [showAddModal, setShowAddModal] = useState(false);

  const { assets, loading: assetsLoading, error: assetsError, refresh } = useAssets(projectId);
  const { findings, loading: findingsLoading } = useFindings(projectId);

  const assetRisk = useMemo(() => {
    const map = new Map<string, string>();
    if (!findings) return map;
    for (const finding of findings) {
      const current = map.get(finding.asset_id);
      const next = finding.severity;
      if (!current || severityRank[next] > severityRank[current]) {
        map.set(finding.asset_id, next);
      }
    }
    return map;
  }, [findings]);

  const lastSeenByAsset = useMemo(() => {
    const map = new Map<string, string>();
    if (!findings) return map;
    for (const finding of findings) {
      const previous = map.get(finding.asset_id);
      if (!previous || new Date(finding.created_at) > new Date(previous)) {
        map.set(finding.asset_id, finding.created_at);
      }
    }
    return map;
  }, [findings]);

  const stats = useMemo(() => {
    const totalAssets = assets?.length || 0;
    const untaggedAssets = assets?.filter((asset) => parseTags(asset.tags).length === 0).length || 0;
    const scannedAssets = assets?.filter((asset) => asset.finding_count > 0).length || 0;
    const highRiskAssets = assets?.filter((asset) => {
      const risk = assetRisk.get(asset.id);
      return risk === 'critical' || risk === 'high';
    }).length || 0;
    return { totalAssets, untaggedAssets, scannedAssets, highRiskAssets };
  }, [assets, assetRisk]);

  return (
    <div className="space-y-8">
      {showAddModal && projectId && (
        <AddAssetModal
          projectId={projectId}
          onClose={() => setShowAddModal(false)}
          onSuccess={refresh}
        />
      )}

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Asset Inventory</h1>
          <p className="text-slate-500 mt-1">Track infrastructure assets and their exposure.</p>
        </div>
        <div className="flex gap-3">
          <button
            title="Import CSV — coming soon"
            disabled
            className="px-4 py-2 bg-white border border-slate-300 text-slate-400 rounded-lg font-medium cursor-not-allowed opacity-50"
          >
            Import CSV
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            disabled={!projectId}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Asset
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Assets</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">
            {assetsLoading ? '...' : stats.totalAssets}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Highly Vulnerable</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">
            {findingsLoading ? '...' : stats.highRiskAssets}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Recently Scanned</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">
            {assetsLoading ? '...' : stats.scannedAssets}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Untagged Assets</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">
            {assetsLoading ? '...' : stats.untaggedAssets}
          </p>
        </div>
      </div>

      {assetsError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {assetsError}
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
            <tr>
              <th className="px-6 py-4">Asset</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Hostname</th>
              <th className="px-6 py-4">IP Address</th>
              <th className="px-6 py-4">Tags</th>
              <th className="px-6 py-4">Last Seen</th>
              <th className="px-6 py-4">Findings</th>
              <th className="px-6 py-4 text-right">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {assetsLoading && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={8}>
                  Loading assets...
                </td>
              </tr>
            )}
            {!assetsLoading && assets?.length === 0 && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={8}>
                  No assets found for this project.
                </td>
              </tr>
            )}
            {!assetsLoading && assets?.map((asset) => {
              const tags = parseTags(asset.tags);
              const risk = assetRisk.get(asset.id) || 'info';
              const lastSeen = lastSeenByAsset.get(asset.id);
              return (
                <tr key={asset.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-900">{asset.identifier}</td>
                  <td className="px-6 py-4 text-slate-600 capitalize">{asset.asset_type}</td>
                  <td className="px-6 py-4 text-slate-600">{asset.hostname || '-'}</td>
                  <td className="px-6 py-4 text-slate-600 font-mono">{asset.ip_address || '-'}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {tags.length === 0 && (
                        <span className="text-xs text-slate-400">No tags</span>
                      )}
                      {tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                      {tags.length > 3 && (
                        <span className="text-xs text-slate-400">+{tags.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-600">
                    {lastSeen ? new Date(lastSeen).toLocaleString() : '—'}
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                      {asset.finding_count}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${severityBadge[risk]}`}>
                      {risk}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
