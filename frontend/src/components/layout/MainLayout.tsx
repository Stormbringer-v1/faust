import type { FC, ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface MainLayoutProps {
  children?: ReactNode;
}

export const MainLayout: FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="bg-background text-on-surface flex min-h-screen font-sans">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0 bg-surface">
        <TopBar />
        <div className="flex-1 overflow-y-auto p-8 space-y-16">
          {children}
        </div>
      </main>
    </div>
  );
};
