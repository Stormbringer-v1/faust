import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { icon: 'dashboard', label: 'Dashboard', path: '/' },
  { icon: 'hard_drive', label: 'Assets', path: '/assets' },
  { icon: 'scanner', label: 'Scans', path: '/scans' },
  { icon: 'warning', label: 'Findings', path: '/findings' },
  { icon: 'description', label: 'Reports', path: '/reports' },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside className="flex flex-col w-64 bg-surface-dim border-r border-transparent ghost-border shrink-0">
      <div className="flex flex-col h-full justify-between p-4">
        <div className="flex flex-col gap-8">
          {/* Logo Area */}
          <div className="flex gap-3 items-center px-2">
            <div 
              className="bg-surface-container-high aspect-square bg-cover rounded-full size-10" 
              title="CyberSec Logo Image" 
              style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBEDRH0FEm52cmDUUj58t6QsLL30EgbC_miuKWQgcBbmO_7ItXVrZ5b9jIjrk4wGaLVxf1FTLvLz1KqFie1XCv85oKUFsn2nKWZnkl7XwSlGaEax6iWg4XCXAnZLzDS1pDNma3iRAN75hIAq92n8QHG1l43ac2HJkWKmgY9a1xOJTR4dmnJPfEIf6po0g490QiK4wbz3fnaNw8b2WinLsfopIVfLPh6zzo4FDsZAElX-29pbtf88CU8nGMz3XgG4lnKWOCkushwWBI")' }}
            ></div>
            <div className="flex flex-col">
              <h1 className="text-on-surface text-base font-bold leading-normal tracking-tight">FAUST</h1>
              <p className="text-on-surface-variant text-[10px] uppercase font-bold leading-normal tracking-wider">Vulnerability Mgmt</p>
            </div>
          </div>
          {/* Navigation Links */}
          <nav className="flex flex-col gap-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.label}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                    isActive ? 'bg-surface-container-high' : 'hover:bg-surface-container'
                  }`}
                >
                  <span 
                    className={`material-symbols-outlined ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}
                    style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
                  >
                    {item.icon}
                  </span>
                  <span className="text-on-surface text-sm font-medium leading-normal">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
        {/* Bottom Setting Link */}
        <div className="flex flex-col gap-2 border-t border-transparent ghost-border pt-4 mt-8">
          <Link to="/settings" className="flex items-center gap-3 px-3 py-2 rounded hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-on-surface-variant">settings</span>
            <span className="text-on-surface text-sm font-medium leading-normal">Settings</span>
          </Link>
        </div>
      </div>
    </aside>
  );
};
