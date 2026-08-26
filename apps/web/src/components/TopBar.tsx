import React, { useState } from 'react';
import {
  Menu,
  Zap,
  Calendar,
  Filter,
  ArrowRight,
  Activity,
  ChevronRight,
  Key,
  ShieldCheck,
  X,
  Check,
} from 'lucide-react';
import { MetricType } from '../types/api';
import { NavSection } from './Sidebar';
import { formatDisplayDate } from '../services/formatters';
import { apiClient } from '../services/api';

interface TopBarProps {
  activeSection: NavSection;
  onOpenMobileMenu: () => void;
  metric: MetricType;
  onChangeMetric: (m: MetricType) => void;
  startDate: string;
  onChangeStartDate: (date: string) => void;
  endDate: string;
  onChangeEndDate: (date: string) => void;
  onRunAnalysis: () => void;
  isLoading: boolean;
}

const SECTION_HEADERS: Record<NavSection, { title: string; subtitle: string; breadcrumb: string }> = {
  overview: {
    title: 'Investigation Overview',
    subtitle: 'Executive summary, key driver attribution, and recommended next steps.',
    breadcrumb: 'Overview',
  },
  anomalies: {
    title: 'What Changed?',
    subtitle: 'Observed metrics compared against baseline expectations to detect anomalies.',
    breadcrumb: 'What Changed',
  },
  'root-cause': {
    title: 'Why It Changed',
    subtitle: 'Volume versus order value decomposition and top contributing segments.',
    breadcrumb: 'Why It Changed',
  },
  'evidence-graph': {
    title: 'Forensic Evidence Graph (DAG)',
    subtitle: 'Interactive Directed Acyclic Graph connecting root cause claims to verified analytical queries.',
    breadcrumb: 'Evidence Graph',
  },
  'challenge-mode': {
    title: 'Executive Challenge Mode',
    subtitle: 'Subject the investigation findings to adversarial scrutiny, counter-hypotheses, and sensitivity audits.',
    breadcrumb: 'Challenge Mode',
  },
  replay: {
    title: 'Investigation Replay',
    subtitle: 'Step-by-step forensic execution playback without non-deterministic re-execution.',
    breadcrumb: 'Replay',
  },
  analytics: {
    title: 'Evidence & Drivers',
    subtitle: 'Multi-dimensional contribution analysis backed by verified analytical marts.',
    breadcrumb: 'Evidence',
  },
  'ai-memo': {
    title: 'Recommendations & Action Plan',
    subtitle: 'Evidence-grounded briefing and prioritized next actions for leadership.',
    breadcrumb: 'Recommendations',
  },
  'autonomous-agent': {
    title: 'Agent Investigation Trace',
    subtitle: 'Chronological multi-step diagnostic trail and automated evidence collection.',
    breadcrumb: 'Agent Trace',
  },
  'data-health': {
    title: 'Data Health & Integrity Checks',
    subtitle: 'Database connection status, mart grain verification, and evidence invariants.',
    breadcrumb: 'Data Health',
  },
};

export const TopBar: React.FC<TopBarProps> = ({
  activeSection,
  onOpenMobileMenu,
  metric,
  onChangeMetric,
  startDate,
  onChangeStartDate,
  endDate,
  onChangeEndDate,
  onRunAnalysis,
  isLoading,
}) => {
  const currentHeader = SECTION_HEADERS[activeSection] || SECTION_HEADERS.overview;
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [apiKeyInput, setApiKeyInput] = useState<string>(apiClient.getApiKey() || '');
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSaveApiKey = () => {
    apiClient.setApiKey(apiKeyInput.trim() || null);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      setShowAuthModal(false);
    }, 800);
  };

  const handleClearApiKey = () => {
    apiClient.setApiKey(null);
    setApiKeyInput('');
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      setShowAuthModal(false);
    }, 800);
  };

  const hasApiKey = Boolean(apiClient.getApiKey());

  return (
    <header className="sticky top-0 z-30 bg-slate-950/95 backdrop-blur-xl border-b border-slate-900 px-4 sm:px-6 lg:px-8 py-3.5">
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        {/* Left Side: Brand, Breadcrumb, and Clear Page Title */}
        <div className="flex items-start space-x-3">
          <button
            onClick={onOpenMobileMenu}
            className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 shrink-0 mt-0.5"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            {/* Global Application Identity + Breadcrumb */}
            <div className="flex items-center space-x-2 text-[11px] font-semibold text-slate-400">
              <div className="w-4 h-4 rounded-md bg-blue-600 flex items-center justify-center">
                <Activity className="w-3 h-3 text-white" />
              </div>
              <span className="font-bold text-slate-300 uppercase tracking-wider">ROOTCAUSE AI</span>
              <ChevronRight className="w-3 h-3 text-slate-600" />
              <span className="text-blue-400 font-medium">{currentHeader.breadcrumb}</span>
            </div>

            {/* Current Page Title */}
            <div className="mt-1">
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {currentHeader.title}
              </h1>
              <p className="text-xs text-slate-400 font-normal mt-0.5">
                {currentHeader.subtitle}
              </p>
            </div>
          </div>
        </div>

        {/* Right Side: Global Controls */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-2.5 sm:p-3 flex flex-wrap items-center gap-3 shadow-sm">
          {/* 1. Metric Selector */}
          <div className="flex flex-col space-y-0.5">
            <label
              htmlFor="metric-select"
              className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1"
            >
              <Filter className="w-3 h-3 text-blue-400" />
              <span>Metric</span>
            </label>
            <div className="relative min-w-[190px]">
              <select
                id="metric-select"
                value={metric}
                onChange={(e) => onChangeMetric(e.target.value as MetricType)}
                className="w-full h-9 pl-3 pr-7 rounded-xl bg-slate-950 border border-slate-750 text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 cursor-pointer appearance-none hover:border-slate-600 transition"
              >
                <option value="total_gmv" className="bg-slate-950 text-white py-1.5 text-xs">
                  Total GMV (Revenue)
                </option>
                <option value="orders_count" className="bg-slate-950 text-white py-1.5 text-xs">
                  Order Volume
                </option>
                <option value="average_order_value" className="bg-slate-950 text-white py-1.5 text-xs">
                  Average Order Value
                </option>
                <option value="late_delivery_rate_pct" className="bg-slate-950 text-white py-1.5 text-xs">
                  Late Delivery Rate
                </option>
                <option value="avg_review_score" className="bg-slate-950 text-white py-1.5 text-xs">
                  Customer Review Score
                </option>
              </select>
              <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400 text-[10px]">
                ▼
              </div>
            </div>
          </div>

          {/* 2. Analysis Period Date Range */}
          <div className="flex flex-col space-y-0.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
              <Calendar className="w-3 h-3 text-indigo-400" />
              <span>Investigation Period</span>
            </label>
            <div className="flex items-center space-x-1.5">
              {/* Start Date */}
              <div className="relative min-w-[125px]">
                <div className="h-9 px-2.5 rounded-xl bg-slate-950 border border-slate-750 hover:border-slate-600 flex items-center justify-between transition focus-within:ring-1 focus-within:ring-blue-500">
                  <div className="flex flex-col">
                    <span className="text-[9px] text-slate-400 uppercase font-bold leading-none">From</span>
                    <span className="text-xs font-semibold text-white font-mono mt-0.5">
                      {formatDisplayDate(startDate)}
                    </span>
                  </div>
                  <Calendar className="w-3.5 h-3.5 text-slate-400 ml-1" />
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => onChangeStartDate(e.target.value)}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                    aria-label="Start Date"
                  />
                </div>
              </div>

              <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />

              {/* End Date */}
              <div className="relative min-w-[125px]">
                <div className="h-9 px-2.5 rounded-xl bg-slate-950 border border-slate-750 hover:border-slate-600 flex items-center justify-between transition focus-within:ring-1 focus-within:ring-blue-500">
                  <div className="flex flex-col">
                    <span className="text-[9px] text-slate-400 uppercase font-bold leading-none">To</span>
                    <span className="text-xs font-semibold text-white font-mono mt-0.5">
                      {formatDisplayDate(endDate)}
                    </span>
                  </div>
                  <Calendar className="w-3.5 h-3.5 text-slate-400 ml-1" />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => onChangeEndDate(e.target.value)}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                    aria-label="End Date"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 3. API Key / Security Button */}
          <div className="flex flex-col space-y-0.5 self-end">
            <button
              onClick={() => setShowAuthModal(true)}
              className={`h-9 px-3 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition ${
                hasApiKey
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                  : 'bg-slate-950 border-slate-750 text-slate-400 hover:text-white hover:border-slate-600'
              }`}
              title="Configure API Key / RBAC Authentication"
            >
              <Key className="w-3.5 h-3.5" />
              <span className="hidden md:inline">{hasApiKey ? 'Authenticated' : 'Auth Key'}</span>
            </button>
          </div>

          {/* 4. Run Analysis Button */}
          <div className="flex flex-col space-y-0.5 self-end">
            <button
              onClick={onRunAnalysis}
              disabled={isLoading}
              className="h-9 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-600/25 flex items-center justify-center space-x-1.5 shrink-0"
            >
              <Zap className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Analyzing...' : 'Run Analysis'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* API Key Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">API Authentication & RBAC</h3>
                  <p className="text-xs text-slate-400">Configure API Key for protected deployments</p>
                </div>
              </div>
              <button
                onClick={() => setShowAuthModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-slate-300 space-y-2 bg-slate-950/70 p-3.5 rounded-xl border border-slate-800">
              <p>
                • <strong>Local / Demo Mode:</strong> When <code className="text-blue-400">AUTH_ENABLED=false</code>, requests execute with default Administrator privileges.
              </p>
              <p>
                • <strong>Protected Mode:</strong> When <code className="text-blue-400">AUTH_ENABLED=true</code>, provide your <code className="text-indigo-400">admin_api_key</code> or <code className="text-indigo-400">analyst_api_key</code> below.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                X-API-Key / Bearer Token
              </label>
              <input
                type="password"
                placeholder="Enter secret API key (e.g. secret_admin_key_123)"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                className="w-full h-10 px-3 rounded-xl bg-slate-950 border border-slate-750 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={handleClearApiKey}
                className="text-xs text-slate-400 hover:text-red-400 transition"
              >
                Clear Key
              </button>
              <div className="flex space-x-2">
                <button
                  onClick={() => setShowAuthModal(false)}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveApiKey}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition flex items-center space-x-1.5 shadow-md shadow-blue-600/30"
                >
                  {savedSuccess ? <Check className="w-4 h-4 text-emerald-400" /> : null}
                  <span>{savedSuccess ? 'Saved!' : 'Save Key'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
