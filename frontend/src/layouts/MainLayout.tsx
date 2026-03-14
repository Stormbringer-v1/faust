import { Outlet, NavLink } from 'react-router-dom';
import { Shield, LayoutDashboard, AlertCircle, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

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
          <h2 className="text-xl font-semibold text-slate-800">Project View</h2>
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
