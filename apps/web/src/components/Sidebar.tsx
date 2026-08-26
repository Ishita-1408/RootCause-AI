import React from 'react';
import {
  LayoutDashboard,
  AlertTriangle,
  Layers,
  Sparkles,
  Compass,
  LineChart,
  Database,
  ShieldCheck,
  Activity,
  Network,
  HelpCircle,
  Clock,
  X,
} from 'lucide-react';

export type NavSection =
  | 'overview'
  | 'anomalies'
  | 'root-cause'
  | 'evidence-graph'
  | 'challenge-mode'
  | 'replay'
  | 'analytics'
  | 'ai-memo'
  | 'autonomous-agent'
  | 'data-health';

interface SidebarProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  apiStatus: 'healthy' | 'unhealthy' | 'checking';
  lastAnalysisTime: string | null;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: NavSection;
  label: string;
  description: string;
  icon: React.ElementType;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
  apiStatus,
  lastAnalysisTime,
  isOpenMobile,
  onCloseMobile,
}) => {
  const investigationItems: NavItem[] = [
    {
      id: 'overview',
      label: 'Overview',
      description: 'Executive summary & story',
      icon: LayoutDashboard,
    },
    {
      id: 'anomalies',
      label: 'What Changed',
      description: 'Unusual changes & timeline',
      icon: AlertTriangle,
    },
    {
      id: 'root-cause',
      label: 'Why It Changed',
      description: 'Primary drivers & levers',
      icon: Layers,
    },
    {
      id: 'evidence-graph',
      label: 'Evidence Graph',
      description: 'Forensic DAG provenance',
      icon: Network,
    },
    {
      id: 'challenge-mode',
      label: 'Challenge Mode',
      description: 'Adversarial hypothesis audit',
      icon: HelpCircle,
    },
    {
      id: 'replay',
      label: 'Investigation Replay',
      description: 'Deterministic step playback',
      icon: Clock,
    },
    {
      id: 'analytics',
      label: 'Evidence',
      description: 'Segment drivers & data',
      icon: LineChart,
    },
    {
      id: 'ai-memo',
      label: 'Recommendations',
      description: 'Actionable leadership steps',
      icon: Sparkles,
    },
  ];

  const systemItems: NavItem[] = [
    {
      id: 'autonomous-agent',
      label: 'Agent Trace',
      description: 'Investigation trail',
      icon: Compass,
    },
    {
      id: 'data-health',
      label: 'Data Health',
      description: 'Integrity & data checks',
      icon: Database,
    },
  ];

  const handleNavClick = (section: NavSection) => {
    onSelectSection(section);
    onCloseMobile();
  };

  const renderNavGroup = (title: string, items: NavItem[]) => (
    <div className="space-y-1">
      <div className="px-3.5 pt-3 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
        {title}
      </div>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = activeSection === item.id;
        return (
          <button
            key={item.id}
            onClick={() => handleNavClick(item.id)}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-left transition-all group ${isActive
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25 font-semibold'
                : 'text-slate-300 hover:bg-slate-900/80 hover:text-white'
              }`}
          >
            <Icon
              className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-blue-400'
                }`}
            />
            <div className="min-w-0 flex-1">
              <div className={`text-xs ${isActive ? 'font-bold text-white' : 'font-medium'}`}>
                {item.label}
              </div>
              <div
                className={`text-[11px] truncate ${isActive ? 'text-blue-100/90 font-normal' : 'text-slate-500 group-hover:text-slate-400'
                  }`}
              >
                {item.description}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-950/95 backdrop-blur-xl border-r border-slate-900 flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${isOpenMobile ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        {/* Top: Brand Header & Nav Groups */}
        <div className="flex-1 overflow-y-auto py-2">
          {/* Brand Header */}
          <div className="p-4 border-b border-slate-900 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-600/20">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-white tracking-wider uppercase">
                  ROOTCAUSE AI
                </h1>
                <p className="text-[11px] text-slate-400 font-medium">Investigation Platform</p>
              </div>
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation Links organized into Investigation & System */}
          <nav className="p-3 space-y-3">
            {renderNavGroup('Investigation', investigationItems)}
            {renderNavGroup('System', systemItems)}
          </nav>
        </div>

        {/* Bottom Section: System Status & Verification */}
        <div className="p-3.5 border-t border-slate-900 space-y-2.5 bg-slate-950/90">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-850 text-xs space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>System Status</span>
              <span
                className={`w-2 h-2 rounded-full ${apiStatus === 'healthy'
                    ? 'bg-emerald-500 animate-pulse'
                    : apiStatus === 'checking'
                      ? 'bg-amber-500'
                      : 'bg-rose-500'
                  }`}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-300">
              <span className="text-slate-400">Data Marts</span>
              <span className="font-mono font-semibold text-slate-200">PostgreSQL</span>
            </div>
            {lastAnalysisTime && (
              <div className="flex items-center justify-between text-[11px] text-slate-300 pt-1 border-t border-slate-800/40">
                <span className="text-slate-400">Last Analysis</span>
                <span className="font-mono text-slate-300">{lastAnalysisTime}</span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-indigo-950/30 text-indigo-300 border border-indigo-900/40 text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="text-[11px]">Evidence Verified (Zero Hallucination)</span>
          </div>
        </div>
      </aside>
    </>
  );
};
