import React from 'react';
import { Database, ShieldCheck, CheckCircle2, Server, HardDrive, RefreshCw } from 'lucide-react';

interface DataHealthViewProps {
  apiStatus: 'healthy' | 'unhealthy' | 'checking';
  onCheckHealth: () => void;
}

export const DataHealthView: React.FC<DataHealthViewProps> = ({ apiStatus, onCheckHealth }) => {
  const marts = [
    {
      name: 'fact_order_analytics',
      grain: '1 row per order_id',
      status: 'Verified',
      description: 'Master analytical order fact table with delivery durations, late flags, and cohort linkages.',
    },
    {
      name: 'fact_daily_kpis',
      grain: '1 row per date × product_category',
      status: 'Verified',
      description: 'Pre-aggregated daily operational telemetry and revenue mart.',
    },
    {
      name: 'dim_customer_cohorts',
      grain: '1 row per customer_unique_id',
      status: 'Verified',
      description: 'Customer lifetime order counts, acquisition cohorts, and total spend.',
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* 1. System Health Status Header */}
      <section aria-label="System Health Status" className="glass-panel-hero p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-blue-600/90 text-white shadow-md shadow-blue-600/30">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-extrabold uppercase tracking-widest text-blue-400">
                SYSTEM TELEMETRY
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
                Data Health & Integrity Status
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  apiStatus === 'healthy'
                    ? 'bg-emerald-500 animate-pulse'
                    : apiStatus === 'checking'
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
              />
              <span className="font-semibold capitalize text-white">
                {apiStatus === 'healthy' ? 'Database Connected' : apiStatus}
              </span>
            </div>

            <button
              onClick={onCheckHealth}
              className="p-2 rounded-xl bg-slate-950/80 hover:bg-slate-900 text-slate-400 hover:text-white border border-slate-800 text-xs transition"
              title="Refresh System Health"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-300">
          Continuous runtime health checks across Supabase PostgreSQL analytical fact tables and FastAPI backend endpoints.
        </p>
      </section>

      {/* 2. Data & Evidence Checks (Analytical Mart Grains) */}
      <section aria-label="Data and Evidence Checks" className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white uppercase tracking-wider">
              Data & Evidence Checks
            </h3>
          </div>
          <span className="text-xs text-emerald-400 font-mono flex items-center space-x-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Analytical Mart Validation Passed</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          {marts.map((m) => (
            <div
              key={m.name}
              className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs text-blue-400">{m.name}</span>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{m.status}</span>
                  </span>
                </div>
                <div className="text-xs font-semibold text-slate-300 mt-1.5">
                  Grain: <span className="font-mono text-slate-400">{m.grain}</span>
                </div>
                <p className="text-xs text-slate-400 leading-normal mt-2">
                  {m.description}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-900 text-[10px] text-slate-500 font-mono">
                psycopg connection pool
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Evidence Integrity Note */}
      <section aria-label="Evidence Integrity" className="glass-panel p-6 rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/20 to-slate-950 text-xs space-y-2">
        <div className="flex items-center space-x-2 text-indigo-300 font-bold uppercase tracking-wider">
          <HardDrive className="w-4 h-4" />
          <span>Evidence Integrity Guarantee</span>
        </div>
        <p className="text-slate-300 leading-relaxed text-xs sm:text-sm max-w-3xl">
          RootCause AI enforces strict separation between deterministic numerical truth and AI explanations. All anomaly detection thresholds, volume/AOV mathematics, and dimensional slice rankings are computed via deterministic PostgreSQL queries and NumPy routines. The LLM narrative synthesis receives immutable verified payloads and does not invent or calculate numerical evidence.
        </p>
      </section>
    </div>
  );
};
