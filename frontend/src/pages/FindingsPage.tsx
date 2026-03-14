export default function FindingsPage() {
  const dummyFindings = [
    { id: 1, title: 'SQL Injection in Login Endpoint', severity: 'Critical', cvss: 9.8, status: 'Open', asset: 'api.example.com' },
    { id: 2, title: 'Unauthenticated API Access', severity: 'High', cvss: 8.5, status: 'Open', asset: 'api.example.com' },
    { id: 3, title: 'Outdated Nginx Version', severity: 'Medium', cvss: 5.3, status: 'Confirmed', asset: 'web-front-01' },
    { id: 4, title: 'TLS 1.1 Support Enabled', severity: 'Low', cvss: 3.7, status: 'Open', asset: 'loadbalancer-eu' },
  ];

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'High': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'Medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'Low': return 'bg-slate-100 text-slate-700 border-slate-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Findings Inventory</h1>
          <p className="text-slate-500 mt-1">All vulnerabilities discovered across monitored assets.</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium transition-colors">
            Export CSV
          </button>
          <button className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors">
            Run Scan
          </button>
        </div>
      </div>

      {/* Basic Data Table Boilerplate */}
      <div className="bg-white border text-sm text-left border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
            <tr>
              <th className="px-6 py-4">Title</th>
              <th className="px-6 py-4">Severity</th>
              <th className="px-6 py-4">CVSS</th>
              <th className="px-6 py-4">Asset</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {dummyFindings.map((finding) => (
              <tr key={finding.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 font-medium text-slate-900">{finding.title}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${getSeverityBadge(finding.severity)}`}>
                    {finding.severity}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-slate-600">{finding.cvss.toFixed(1)}</td>
                <td className="px-6 py-4 text-slate-600">{finding.asset}</td>
                <td className="px-6 py-4 text-slate-600">
                  <span className="px-2 py-1 bg-slate-100 text-xs rounded-md font-medium text-slate-700">
                    {finding.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right text-brand-600 font-medium cursor-pointer hover:text-brand-800">
                  View Details
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
