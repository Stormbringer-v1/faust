import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

type Tab = 'profile' | 'scanners' | 'ai' | 'notifications';

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('profile');

  const tabs: { id: Tab; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'scanners', label: 'Scanners' },
    { id: 'ai', label: 'AI Provider' },
    { id: 'notifications', label: 'Notifications' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Manage your account, scanner configuration, and AI providers.</p>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 max-w-lg">
          <h2 className="text-base font-semibold text-slate-900">Account Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                defaultValue={user?.full_name || ''}
                disabled
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                defaultValue={user?.email || ''}
                disabled
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
              <span className="inline-block px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-semibold border border-brand-200 capitalize">
                {user?.role || 'viewer'}
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-400">Profile editing will be available in a future release.</p>
        </div>
      )}

      {/* Scanners Tab */}
      {activeTab === 'scanners' && (
        <div className="space-y-4 max-w-lg">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-slate-900">Scanner Configuration</h2>
            <div className="space-y-3">
              {[
                { name: 'Nmap', description: 'Network host and port discovery', status: 'Available' },
                { name: 'Nuclei', description: 'Web application vulnerability scanning', status: 'Available' },
                { name: 'Trivy', description: 'Container and cloud misconfiguration scanning', status: 'Available' },
                { name: 'Custom DAST', description: 'Faust built-in web application scanner', status: 'Coming Soon' },
              ].map((scanner) => (
                <div key={scanner.name} className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{scanner.name}</p>
                    <p className="text-xs text-slate-500">{scanner.description}</p>
                  </div>
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
                    scanner.status === 'Available'
                      ? 'bg-green-50 text-green-700 border-green-200'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}>
                    {scanner.status}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-400">Scanner binaries are pre-installed in the Docker container. Per-scan config is set in the Scans page.</p>
          </div>
        </div>
      )}

      {/* AI Provider Tab */}
      {activeTab === 'ai' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 max-w-lg">
          <h2 className="text-base font-semibold text-slate-900">AI Remediation Provider</h2>
          <p className="text-sm text-slate-500">
            FAUST uses AI to generate OS-specific remediation instructions for findings. Configure your preferred provider via environment variables in your deployment.
          </p>
          <div className="space-y-3">
            {[
              { name: 'Anthropic (Claude)', envVar: 'ANTHROPIC_API_KEY' },
              { name: 'OpenAI (GPT-4)', envVar: 'OPENAI_API_KEY' },
              { name: 'Google (Gemini)', envVar: 'GOOGLE_API_KEY' },
              { name: 'Local (Ollama)', envVar: 'OLLAMA_BASE_URL' },
            ].map((provider) => (
              <div key={provider.name} className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{provider.name}</p>
                  <code className="text-xs text-slate-400 font-mono">{provider.envVar}</code>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400">
            Set the relevant env vars in your <code className="font-mono">.env</code> file and restart the backend container. The AI module auto-selects a configured provider.
          </p>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 max-w-lg">
          <h2 className="text-base font-semibold text-slate-900">Notifications</h2>
          <p className="text-sm text-slate-500 mt-2">
            Email and webhook notifications are planned for a future release. Check back soon.
          </p>
          <div className="mt-6 flex items-center gap-3 p-4 bg-brand-50 rounded-lg border border-brand-100">
            <span className="text-2xl">🔔</span>
            <p className="text-sm text-brand-700 font-medium">Coming in Phase 4</p>
          </div>
        </div>
      )}
    </div>
  );
}
