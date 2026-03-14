import type { FC } from 'react';

interface Asset {
  id: string;
  name?: string;
  identifier: string;
  asset_type: string;
  created_at: string;
}

interface Props {
  assets?: Asset[];
  loading?: boolean;
}

export const TopAssetsTable: FC<Props> = ({ assets = [], loading = false }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden pb-4">
      <div className="p-6 pb-2 border-b border-slate-200 border-opacity-50 flex justify-between items-center">
        <h3 className="text-slate-800 text-xl font-semibold">Top Assets</h3>
        <button className="text-brand-600 text-sm font-medium hover:text-brand-700 transition-colors flex items-center gap-1">
          View All Inventory
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </button>
      </div>
      <div className="w-full overflow-x-auto px-6">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-slate-500 text-xs uppercase tracking-wider">
              <th className="py-4 font-medium">Asset Name / ID</th>
              <th className="py-4 font-medium">Type</th>
              <th className="py-4 font-medium">Created</th>
              <th className="py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {loading ? (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-500">Loading assets...</td>
              </tr>
            ) : assets.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-500">No assets found.</td>
              </tr>
            ) : (
              assets.slice(0, 5).map((asset) => (
                <tr key={asset.id} className="group border-b border-slate-100 last:border-0">
                  <td className="py-4">
                    <div className="font-medium text-slate-800">{asset.name || asset.identifier}</div>
                    <div className="text-slate-500 text-xs font-mono">{asset.identifier}</div>
                  </td>
                  <td className="py-4">
                    <span className="inline-flex items-center px-2 py-1 rounded bg-slate-100 text-slate-700 text-[10px] font-bold uppercase tracking-wide">
                      {asset.asset_type}
                    </span>
                  </td>
                  <td className="py-4 text-slate-600">
                    {new Date(asset.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-4 text-right">
                    <button className="text-slate-400 hover:text-brand-600 transition-colors">
                      <span className="material-symbols-outlined text-[18px]">more_vert</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
