import React from 'react';
import { Activity, ShieldCheck, Zap } from 'lucide-react';

interface HeaderProps {
  apiStatus: 'healthy' | 'unhealthy' | 'checking';
  onRefresh: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ apiStatus, onRefresh, isLoading }) => {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Identity */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">RootCause AI</h1>
              <span className="text-[11px] uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                Live Analytics
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Business Diagnostics & Evidence-Backed Decision Support
            </p>
          </div>
        </div>

        {/* Global Controls & Status */}
        <div className="flex items-center space-x-3">
          {/* API Health Badge */}
          <div className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                apiStatus === 'healthy'
                  ? 'bg-emerald-500 animate-pulse'
                  : apiStatus === 'checking'
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300 font-medium capitalize">
              {apiStatus === 'healthy' ? 'System Online' : apiStatus === 'checking' ? 'Connecting...' : 'Database Offline'}
            </span>
          </div>

          {/* Architecture Guardrail Indicator */}
          <div className="hidden sm:flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-indigo-950/40 text-indigo-300 border border-indigo-800/50">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Deterministic Grounding</span>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center space-x-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-600/20"
          >
            <Zap className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Analyzing...' : 'Run Analysis'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

