import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { type ReactElement } from 'react';
import Layout from './layouts/MainLayout';
import DashboardPage from './pages/DashboardPage';
import FindingsPage from './pages/FindingsPage';
import AssetsPage from './pages/Assets';
import ScansPage from './pages/Scans';
import ReportsPage from './pages/Reports';
import SettingsPage from './pages/Settings';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ProjectProvider } from './contexts/ProjectContext';

function ProtectedRoute({ children }: { children: ReactElement }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <ProjectProvider>{children}</ProjectProvider>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="assets" element={<AssetsPage />} />
            <Route path="scans" element={<ScansPage />} />
            <Route path="findings" element={<FindingsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
