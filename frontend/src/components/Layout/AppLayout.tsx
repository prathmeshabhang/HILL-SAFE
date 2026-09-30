import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { TopNav } from './TopNav';
import { Sidebar } from './Sidebar';
import { EmergencyBanner } from './EmergencyBanner';
import { useUiStore } from '../../store/useUiStore';
import { PanelLeft } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const {
    sidebarPinned,
    sidebarOpen,
    toggleSidebar,
    setSidebarOpen,
  } = useUiStore();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 transition-colors">
      <TopNav />
      {location.pathname === '/' && <EmergencyBanner />}

      <div className="flex-1 flex relative">
        {/* Floating Quick Menu Toggle Button when sidebar is hidden */}
        {!sidebarPinned && !sidebarOpen && (
          <button
            onClick={toggleSidebar}
            title="Open Navigation Menu"
            className="fixed top-20 left-2 z-30 px-2.5 py-1.5 rounded-xl bg-white/95 dark:bg-slate-900/95 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 shadow-lg hover:text-blue-500 hover:border-blue-500/40 hover:scale-105 transition flex items-center gap-1.5 text-xs font-semibold group cursor-pointer"
          >
            <PanelLeft className="w-4 h-4 text-blue-500 group-hover:rotate-12 transition-transform" />
            <span className="text-[11px] font-medium hidden sm:inline">Menu</span>
          </button>
        )}

        {/* Sidebar Component */}
        <Sidebar />

        {/* Main Content Area:
            - When sidebar is hidden/unpinned (default): ml-0 (100% full screen for maps & charts!)
            - When sidebar is pinned: lg:ml-64 */}
        <main
          onClick={() => {
            if (sidebarOpen && !sidebarPinned) {
              setSidebarOpen(false);
            }
          }}
          className={`flex-1 transition-[margin-left] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] p-4 sm:p-6 lg:p-8 flex flex-col min-w-0 ${
            sidebarPinned ? 'lg:ml-64' : 'ml-0'
          }`}
        >
          {/* Animated Page Transition Container */}
          <div key={location.pathname} className="page-enter-animation flex-1 flex flex-col min-w-0">
            <Outlet />
          </div>

          {/* Institutional Footer */}
          <footer className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
            <div>
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                HILL-SAFE v4.0.0
              </span>{' '}
              — Upper Beas Basin Flash Flood & Natural Dam Early Warning System
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono">
              <span>H.P. SDMA Operational Prototype</span>
              <span>•</span>
              <span className="text-amber-500">PROTOTYPE_STAGING</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
};
