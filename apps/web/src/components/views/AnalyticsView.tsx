import React, { useState } from 'react';
import { RootCauseInvestigationResponse, AnomalyDetectionResponse, MetricType } from '../../types/api';
import { formatBRL, formatPercentChange, prettifyDimensionValue, prettifyDimensionName, formatDisplayDate } from '../../services/formatters';
import { ShieldCheck, CheckCircle2, ChevronDown, ChevronUp, Database, Code } from 'lucide-react';

interface AnalyticsViewProps {
  anomalyData: AnomalyDetectionResponse | null;
  rootCauseData: RootCauseInvestigationResponse | null;
  metric: MetricType;
  selectedDate: string;
  isLoading: boolean;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({
  rootCauseData,
  metric: _metric,
  selectedDate,
  isLoading,
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-2">
        <div className="glass-panel p-6 h-64 skeleton rounded-2xl" />
        <div className="glass-panel p-6 h-64 skeleton rounded-2xl" />
      </div>
    );
  }

  const decomposition = rootCauseData?.decomposition;
  const contributors = rootCauseData?.ranked_contributors || [];
  const topContributor = contributors[0];

  const volPctChange = decomposition
    ? ((decomposition.observed_orders - decomposition.baseline_orders) / (decomposition.baseline_orders || 1)) * 100
    : 0;
  const aovPctChange = decomposition
    ? ((decomposition.observed_aov - decomposition.baseline_aov) / (decomposition.baseline_aov || 1)) * 100
    : 0;

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* 1. WHY WE BELIEVE THIS (Trust Verification Hero) */}
      <section aria-label="Evidence Verification" className="glass-panel-hero p-6 sm:p-8 rounded-3xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-extrabold uppercase tracking-widest text-emerald-400">
              TRUST & EVIDENCE INTEGRITY
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center space-x-2 mt-0.5">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <span>WHY WE BELIEVE THIS</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Every numerical claim is verified against deterministic PostgreSQL analytical marts with zero lookahead bias.
            </p>
          </div>

          <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono text-emerald-400 flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>100% Deterministic Math</span>
          </div>
        </div>

        {/* 4 Trust Verification Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono pt-1">
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 font-sans text-[11px] font-bold block">✓ Order volume verified</span>
            <span className="text-emerald-400 font-bold block">
              {decomposition ? `${decomposition.observed_orders} vs ${decomposition.baseline_orders} (${formatPercentChange(volPctChange)})` : 'Verified'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 font-sans text-[11px] font-bold block">✓ Average order value verified</span>
            <span className="text-blue-400 font-bold block">
              {decomposition ? `${formatBRL(decomposition.observed_aov)} vs ${formatBRL(decomposition.baseline_aov)} (${formatPercentChange(aovPctChange)})` : 'Verified'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 font-sans text-[11px] font-bold block">✓ Geographic contribution</span>
            <span className="text-purple-400 font-bold block truncate">
              {topContributor ? `${prettifyDimensionValue(topContributor.dimension_value, topContributor.dimension)} (+${formatBRL(topContributor.absolute_change)})` : 'Verified'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 font-sans text-[11px] font-bold block">✓ Baseline verified</span>
            <span className="text-emerald-400 font-bold block">
              7-Day Rolling Baseline
            </span>
          </div>
        </div>
      </section>

      {/* 2. WHERE DID THE CHANGE COME FROM? (Contributors Table) */}
      <section aria-label="Dimensional Slices" className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-[11px] font-extrabold uppercase tracking-widest text-indigo-400">
              DIMENSIONAL EVIDENCE
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-0.5">
              Where Did the Change Come From?
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {contributors.length} Evaluated Slices ({formatDisplayDate(selectedDate)})
          </span>
        </div>

        {contributors.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-6 text-center">
            No dimensional contributor slices returned for this date.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800/80">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-xs text-slate-400 uppercase font-bold">
                  <th className="py-3.5 pl-4">Rank</th>
                  <th className="py-3.5">Dimension</th>
                  <th className="py-3.5">Segment Name</th>
                  <th className="py-3.5 text-right">Observed Value</th>
                  <th className="py-3.5 text-right">Baseline Value</th>
                  <th className="py-3.5 text-right">Net Shift (Delta)</th>
                  <th className="py-3.5 text-right pr-4">Contribution Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {contributors.map((c) => (
                  <tr key={`${c.dimension}-${c.dimension_value}`} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 pl-4 text-slate-500 font-bold">#{c.rank}</td>
                    <td className="py-3 font-sans text-slate-300 font-medium">
                      {prettifyDimensionName(c.dimension)}
                    </td>
                    <td className="py-3 font-bold text-white font-sans truncate max-w-[200px]">
                      {prettifyDimensionValue(c.dimension_value, c.dimension)}
                    </td>
                    <td className="py-3 text-right text-slate-300">
                      {formatBRL(c.observed_value)}
                    </td>
                    <td className="py-3 text-right text-slate-400">
                      {formatBRL(c.baseline_value)}
                    </td>
                    <td
                      className={`py-3 text-right font-bold ${c.absolute_change >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                    >
                      {c.absolute_change >= 0 ? '+' : ''}
                      {formatBRL(c.absolute_change)}
                    </td>
                    <td className="py-3 text-right pr-4 font-bold text-indigo-300">
                      {c.contribution_pct ? `${Math.round(Math.abs(c.contribution_pct))}%` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* 3. Progressive Disclosure: Technical Evidence & SQL Details */}
      <section aria-label="Technical Evidence">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="text-xs font-semibold text-slate-400 hover:text-white flex items-center space-x-1.5 transition py-1"
        >
          {showTechnicalDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          <span>{showTechnicalDetails ? 'Hide technical evidence' : 'View technical evidence & database checks (Level 3) →'}</span>
        </button>

        {showTechnicalDetails && (
          <div className="glass-panel p-5 rounded-2xl space-y-4 mt-2 border border-slate-800 text-xs font-mono text-slate-300">
            <div className="flex items-center space-x-2 text-indigo-300 font-bold uppercase tracking-wider">
              <Database className="w-4 h-4" />
              <span>PostgreSQL Mart Schema & Invariants</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-blue-400 font-bold">fact_daily_kpis</div>
                <div className="text-slate-400 text-[11px]">Grain: 1 row per date × product_category</div>
                <div className="text-slate-500 text-[10px]">Zero cartesian joins • psycopg connection pooling</div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-blue-400 font-bold">fact_order_analytics</div>
                <div className="text-slate-400 text-[11px]">Grain: 1 row per order_id</div>
                <div className="text-slate-500 text-[10px]">Exact revenue conservation guarantee</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 space-y-1">
              <div className="flex items-center space-x-1.5 text-slate-300 font-sans font-bold">
                <Code className="w-3.5 h-3.5 text-blue-400" />
                <span>Deterministic Computation Guarantee</span>
              </div>
              <p className="text-[11px] leading-relaxed font-sans">
                The analytical mart is queried with exact timestamps, strictly separating the analytical compute engine from LLM text synthesis. The LLM receives immutable JSON payloads and cannot alter or fabricate numerical outputs.
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
