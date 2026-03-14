import { useState } from 'react';
import api from '../services/api';
import { useProject } from '../contexts/ProjectContext';
import { useReports } from '../hooks/useReports';

const formatOptions = [
  { value: 'pdf', label: 'PDF', description: 'Formatted PDF document via WeasyPrint.' },
  { value: 'html', label: 'HTML', description: 'Standalone HTML report.' },
  { value: 'json', label: 'JSON', description: 'Structured JSON data export.' },
  { value: 'csv', label: 'CSV', description: 'Spreadsheet-compatible CSV.' },
];

const statusBadge: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  generating: 'bg-blue-100 text-blue-700 border-blue-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  failed: 'bg-red-100 text-red-700 border-red-200',
};

export default function ReportsPage() {
  const { selectedProject } = useProject();
  const projectId = selectedProject?.id;
  const { reports, loading, error: fetchError, refresh } = useReports(projectId);

  const [title, setTitle] = useState('');
  const [format, setFormat] = useState('pdf');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!projectId) {
      setFormError('No project available. Create a project first.');
      return;
    }
    if (!title.trim()) {
      setFormError('Report title is required.');
      return;
    }
    setSubmitting(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      await api.post(`/projects/${projectId}/reports/`, {
        title: title.trim(),
        report_format: format,
      });
      setFormSuccess('Report generation queued. It will appear in the list below.');
      setTitle('');
      await refresh();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to queue report generation');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = async (reportId: string, reportTitle: string, reportFormat: string) => {
    if (!projectId) return;
    setDownloading(reportId);
    try {
      const response = await api.get(
        `/projects/${projectId}/reports/${reportId}/download`,
        { responseType: 'blob' }
      );
      const mimeTypes: Record<string, string> = {
        pdf: 'application/pdf',
        html: 'text/html',
        json: 'application/json',
        csv: 'text/csv',
      };
      const blob = new Blob([response.data], {
        type: mimeTypes[reportFormat] || 'application/octet-stream',
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${reportTitle}.${reportFormat}`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Download failed — report may not be ready yet.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports</h1>
        <p className="text-slate-500 mt-1">Generate and download vulnerability reports for your project.</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6">
        <h2 className="text-lg font-semibold text-slate-900">Generate New Report</h2>

        {(formError || formSuccess) && (
          <div className={`rounded-lg border px-4 py-3 text-sm ${formError ? 'border-red-200 bg-red-50 text-red-700' : 'border-green-200 bg-green-50 text-green-700'}`}>
            {formError || formSuccess}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Report Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            placeholder="e.g. Q1 2026 Vulnerability Assessment"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">Format</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {formatOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setFormat(opt.value)}
                className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                  format === opt.value
                    ? 'border-brand-500 bg-brand-50'
                    : 'border-slate-200 hover:border-brand-200'
                }`}
              >
                <p className="text-sm font-semibold text-slate-900">{opt.label}</p>
                <p className="text-xs text-slate-500 mt-1">{opt.description}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={submitting}
            className="px-6 py-2 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Queuing...' : 'Generate Report'}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700">Generated Reports</h2>
          <button
            onClick={refresh}
            className="text-xs text-brand-600 hover:text-brand-700 font-medium"
          >
            Refresh
          </button>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
            <tr>
              <th className="px-6 py-4">Title</th>
              <th className="px-6 py-4">Format</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={5}>Loading reports...</td>
              </tr>
            )}
            {fetchError && !loading && (
              <tr>
                <td className="px-6 py-6 text-red-600" colSpan={5}>{fetchError}</td>
              </tr>
            )}
            {!loading && reports.length === 0 && (
              <tr>
                <td className="px-6 py-6 text-slate-500" colSpan={5}>No reports yet. Generate one above.</td>
              </tr>
            )}
            {!loading && reports.map((report) => (
              <tr key={report.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 font-medium text-slate-900">{report.title}</td>
                <td className="px-6 py-4 uppercase text-xs font-bold text-slate-600">{report.report_format}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${statusBadge[report.status] || statusBadge.pending}`}>
                    {report.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-600">{new Date(report.created_at).toLocaleString()}</td>
                <td className="px-6 py-4">
                  {report.status === 'completed' ? (
                    <button
                      onClick={() => handleDownload(report.id, report.title, report.report_format)}
                      disabled={downloading === report.id}
                      className="text-xs font-semibold text-brand-600 hover:text-brand-700 disabled:opacity-50"
                    >
                      {downloading === report.id ? 'Downloading...' : 'Download'}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-400">
                      {report.status === 'failed'
                        ? (report.error_message?.slice(0, 60) || 'Failed')
                        : '—'}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
