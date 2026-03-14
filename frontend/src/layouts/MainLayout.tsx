import { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Shield, LayoutDashboard, AlertCircle, Settings, LogOut, Radar, Server, FileText, ChevronDown, Plus, FolderOpen } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useProject } from '../contexts/ProjectContext';

function ProjectSelector() {
  const { projects, selectedProject, setSelectedProject, createProject } = useProject();
  const [open, setOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targets, setTargets] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) { setCreateError('Name is required.'); return; }
    setCreating(true);
    setCreateError(null);
    try {
      const parsed = targets.split(',').map((t) => t.trim()).filter(Boolean);
      await createProject(name.trim(), description.trim(), parsed);
      setName(''); setDescription(''); setTargets('');
      setShowCreate(false);
      setOpen(false);
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-700 hover:bg-slate-50 transition-colors"
      >
        <FolderOpen className="w-4 h-4 text-brand-500" />
        <span className="max-w-[160px] truncate font-medium">
          {selectedProject ? selectedProject.name : 'No project'}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-white border border-slate-200 rounded-xl shadow-lg z-50">
          {projects.length > 0 && (
            <ul className="py-1 max-h-48 overflow-auto">
              {projects.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => { setSelectedProject(p); setOpen(false); }}
                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 transition-colors ${
                      selectedProject?.id === p.id ? 'text-brand-600 font-semibold' : 'text-slate-700'
                    }`}
                  >
                    {p.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {projects.length > 0 && <div className="border-t border-slate-100" />}

          {!showCreate ? (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 w-full px-4 py-3 text-sm text-brand-600 hover:bg-brand-50 transition-colors font-medium"
            >
              <Plus className="w-4 h-4" />
              New project
            </button>
          ) : (
            <div className="p-4 space-y-3">
              <p className="text-xs font-semibold text-slate-700 uppercase tracking-wide">New Project</p>
              {createError && (
                <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1">{createError}</p>
              )}
              <input
                autoFocus
                type="text"
                placeholder="Project name *"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
              <input
                type="text"
                placeholder="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
              <input
                type="text"
                placeholder="Allowed targets, e.g. 192.168.1.0/24"
                value={targets}
                onChange={(e) => setTargets(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
              <p className="text-xs text-slate-400">Comma-separated CIDRs. Can be set later.</p>
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={creating}
                  className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
                <button
                  onClick={() => { setShowCreate(false); setCreateError(null); }}
                  className="flex-1 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MainLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen w-full bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-800 bg-slate-950">
          <Shield className="w-6 h-6 text-brand-500 mr-3" />
          <span className="text-lg font-bold text-white tracking-wide">FAUST</span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <LayoutDashboard className="w-5 h-5 mr-3" />
            Dashboard
          </NavLink>
          <NavLink
            to="/scans"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Radar className="w-5 h-5 mr-3" />
            Scans
          </NavLink>
          <NavLink
            to="/assets"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Server className="w-5 h-5 mr-3" />
            Assets
          </NavLink>
          <NavLink
            to="/findings"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <AlertCircle className="w-5 h-5 mr-3" />
            Findings
          </NavLink>
          <NavLink
            to="/reports"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-brand-600 text-white' : 'hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <FileText className="w-5 h-5 mr-3" />
            Reports
          </NavLink>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button className="flex items-center w-full px-4 py-3 text-sm hover:bg-slate-800 hover:text-white rounded-lg transition-colors mb-1">
            <Settings className="w-5 h-5 mr-3" />
            Settings
          </button>
          <button
            onClick={logout}
            className="flex items-center w-full px-4 py-3 text-sm hover:bg-red-900/50 hover:text-red-400 rounded-lg transition-colors text-slate-400"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Log out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8">
          <ProjectSelector />
          <div className="flex items-center space-x-4">
            <div className="flex items-center justify-center space-x-2">
              <span className="text-sm font-medium text-slate-600">{user?.full_name || user?.email}</span>
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 font-bold">
                {user?.full_name ? user.full_name[0].toUpperCase() : (user?.email ? user.email[0].toUpperCase() : 'U')}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
