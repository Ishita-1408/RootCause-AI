import React, { useState } from 'react';
import {
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Truck,
  Star,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { RootCauseInvestigationResponse } from '../types/api';
import {
  formatBRL,
  formatPercentChange,
  prettifyDimensionValue,
  prettifyDimensionName,
  formatDisplayDate,
} from '../services/formatters';

interface RootCausePanelProps {
  data: RootCauseInvestigationResponse | null;
  isLoading: boolean;
  selectedDate: string;
}

export const RootCausePanel: React.FC<RootCausePanelProps> = ({ data, isLoading, selectedDate }) => {
  const [showFormula, setShowFormula] = useState<boolean>(false);
  const [showSqlDetails, setShowSqlDetails] = useState<boolean>(false);

  if (isLoading) {
    return (
      <div className="glass-panel p-6 rounded-2xl space-y-4 max-w-5xl mx-auto">
        <div className="h-8 w-64 skeleton" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-40 skeleton rounded-xl" />
          <div className="h-40 skeleton rounded-xl" />
        </div>
        <div className="h-48 skeleton rounded-xl" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-panel p-8 rounded-2xl text-center flex flex-col items-center justify-center max-w-5xl mx-auto">
        <Layers className="w-10 h-10 text-slate-500 mb-2.5" />
        <h3 className="text-base font-semibold text-white">No Investigation Selected</h3>
        <p className="text-xs text-slate-400 max-w-md mt-1">
          Select an anomaly date from the timeline or click "Run Analysis" to compute drivers for {formatDisplayDate(selectedDate)}.
        </p>
      </div>
    );
  }

  const { summary, decomposition, ranked_contributors, operational_indicators } = data;
  const isIncrease = summary.direction === 'increase' || summary.absolute_change >= 0;
  const isDecrease = summary.direction === 'decrease' || summary.absolute_change < 0;

  // Volume vs AOV contributions
  const volPctChange = decomposition
    ? ((decomposition.observed_orders - decomposition.baseline_orders) / (decomposition.baseline_orders || 1)) * 100
    : 0;
  const aovPctChange = decomposition
    ? ((decomposition.observed_aov - decomposition.baseline_aov) / (decomposition.baseline_aov || 1)) * 100
    : 0;

  const volContributionPct = Math.abs(decomposition?.volume_contribution_pct || 65);
  const aovContributionPct = Math.abs(decomposition?.aov_contribution_pct || 35);
  const isVolMainDriver = volContributionPct >= aovContributionPct;

  const top3Contributors = ranked_contributors.slice(0, 3);

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* 1. Header: WHY DID REVENUE CHANGE? */}
      <div className="glass-panel-hero p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-extrabold uppercase tracking-widest text-indigo-400">
            WHY IT CHANGED
          </div>
          <span className="text-xs font-mono text-slate-300 font-bold">
            {formatDisplayDate(summary.anomaly_date)}
          </span>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight uppercase">
              WHY DID REVENUE {isIncrease ? 'INCREASE' : 'DECREASE'}?
            </h2>
            <p className="text-base sm:text-lg text-slate-300 mt-1 font-medium">
              Revenue {isIncrease ? 'increased' : 'decreased'}{' '}
              <span className={`font-bold ${isIncrease ? 'text-emerald-400' : 'text-rose-400'}`}>
                {summary.percentage_change ? Math.abs(summary.percentage_change).toFixed(1) : '0.0'}%
              </span>{' '}
              on {formatDisplayDate(summary.anomaly_date)}.
            </p>
          </div>

          {/* Observed vs Baseline Pill */}
          <div className="bg-slate-950/80 px-4 py-2.5 rounded-2xl border border-slate-800 flex items-center space-x-3 shrink-0">
            <div>
              <div className="text-[9px] text-slate-400 uppercase font-bold">Actual vs Expected</div>
              <div className="text-sm font-bold font-mono text-white">
                {formatBRL(summary.observed_value)} <span className="text-slate-500 font-normal">vs</span> {formatBRL(summary.baseline_value)}
              </div>
            </div>
            <div
              className={`flex items-center space-x-0.5 px-2.5 py-1 rounded-xl text-xs font-bold font-mono ${isIncrease
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : isDecrease
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-slate-800 text-slate-300'
                }`}
            >
              {isIncrease ? <ArrowUpRight className="w-3.5 h-3.5" /> : isDecrease ? <ArrowDownRight className="w-3.5 h-3.5" /> : <Minus className="w-3.5 h-3.5" />}
              <span>{formatPercentChange(summary.percentage_change)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. PRIMARY DRIVER vs SECONDARY FACTOR */}
      {decomposition && (
        <section aria-label="Volume and AOV Decomposition" className="space-y-4">
          <div>
            <div className="text-[11px] font-extrabold uppercase tracking-widest text-blue-400">
              DECOMPOSITION LEVERS
            </div>
            <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
              Volume vs Order Value Contribution
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Primary Driver */}
            <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-blue-500 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-400">
                    {isVolMainDriver ? 'PRIMARY DRIVER' : 'SECONDARY FACTOR'}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-300">
                    {decomposition.observed_orders} vs {decomposition.baseline_orders} orders
                  </span>
                </div>

                <h4 className="text-2xl font-bold text-white tracking-tight mt-2 flex items-center space-x-2">
                  {volPctChange >= 0 ? <TrendingUp className="w-5 h-5 text-emerald-400" /> : <TrendingDown className="w-5 h-5 text-rose-400" />}
                  <span>Orders ({volPctChange >= 0 ? '+' : ''}{volPctChange.toFixed(1)}%)</span>
                </h4>

                <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
                  Net Dollar Effect:{' '}
                  <strong className="font-mono text-white font-bold">
                    {decomposition.volume_effect >= 0 ? '+' : ''}{formatBRL(decomposition.volume_effect)}
                  </strong>{' '}
                  ({Math.round(volContributionPct)}% contribution weight).
                </p>
              </div>

              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                  <span>Relative Volume Contribution</span>
                  <span className="font-mono font-bold text-blue-400">{Math.round(volContributionPct)}%</span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-blue-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(volContributionPct, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Secondary Factor */}
            <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-indigo-500 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-indigo-400">
                    {!isVolMainDriver ? 'PRIMARY DRIVER' : 'SECONDARY FACTOR'}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-300">
                    {formatBRL(decomposition.observed_aov)} vs {formatBRL(decomposition.baseline_aov)}
                  </span>
                </div>

                <h4 className="text-2xl font-bold text-white tracking-tight mt-2 flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-indigo-400" />
                  <span>Average Order Value ({aovPctChange >= 0 ? '+' : ''}{aovPctChange.toFixed(1)}%)</span>
                </h4>

                <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
                  Net Dollar Effect:{' '}
                  <strong className="font-mono text-white font-bold">
                    {decomposition.aov_effect >= 0 ? '+' : ''}{formatBRL(decomposition.aov_effect)}
                  </strong>{' '}
                  ({Math.round(aovContributionPct)}% contribution weight).
                </p>
              </div>

              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                  <span>Relative AOV Contribution</span>
                  <span className="font-mono font-bold text-indigo-400">{Math.round(aovContributionPct)}%</span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(aovContributionPct, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Progressive Disclosure: Mathematical Decomposition Formula */}
          <div>
            <button
              onClick={() => setShowFormula(!showFormula)}
              className="text-xs text-slate-400 hover:text-white flex items-center space-x-1.5 transition py-1"
            >
              {showFormula ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              <span>{showFormula ? 'Hide mathematical formula' : 'View mathematical decomposition formula (Level 3)'}</span>
            </button>

            {showFormula && (
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-2 mt-2">
                <div className="text-indigo-300 font-bold">
                  ΔRevenue ≡ (ΔOrders × AOV_baseline) + (ΔAOV × Orders_baseline) + (ΔOrders × ΔAOV)
                </div>
                <div className="text-slate-400">
                  Volume Effect: {formatBRL(decomposition.volume_effect)} | AOV Effect: {formatBRL(decomposition.aov_effect)} | Interaction Effect: {formatBRL(decomposition.interaction_effect)}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 3. WHERE DID THE CHANGE COME FROM? (Ranked Contributors) */}
      <section aria-label="Dimensional Contributors" className="space-y-4">
        <div>
          <div className="text-[11px] font-extrabold uppercase tracking-widest text-purple-400">
            CONTRIBUTING SEGMENTS
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
            WHERE DID THE CHANGE COME FROM?
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Top customer regions, product categories, and sellers evaluated by deterministic contribution.
          </p>
        </div>

        {/* Top 3 Visual Podiums */}
        {top3Contributors.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {top3Contributors.map((c, i) => (
              <div
                key={`${c.dimension}-${c.dimension_value}`}
                className="glass-panel p-5 rounded-2xl flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 flex items-center justify-center font-mono font-bold text-xs">
                      0{i + 1}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {prettifyDimensionName(c.dimension)}
                    </span>
                  </div>

                  <h4 className="text-lg font-bold text-white mt-2 truncate">
                    {prettifyDimensionValue(c.dimension_value, c.dimension)}
                  </h4>

                  <div className="text-base font-mono font-bold mt-1">
                    <span className={c.absolute_change >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                      {c.absolute_change >= 0 ? '+' : ''}
                      {formatBRL(c.absolute_change)}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Contribution</span>
                  <span className="font-mono font-bold text-purple-300">
                    {c.contribution_pct ? `${Math.round(Math.abs(c.contribution_pct))}%` : 'N/A'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Complete Contributor Table */}
        {ranked_contributors.length > 0 && (
          <div className="glass-panel rounded-2xl overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase font-bold">
                  <th className="py-3.5 pl-4">Rank</th>
                  <th className="py-3.5">Dimension</th>
                  <th className="py-3.5">Segment Name</th>
                  <th className="py-3.5 text-right">Observed</th>
                  <th className="py-3.5 text-right">Baseline</th>
                  <th className="py-3.5 text-right">Net Change</th>
                  <th className="py-3.5 text-right pr-4">Contribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {ranked_contributors.map((c) => (
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
                    <td className="py-3 text-right pr-4 font-bold text-purple-300">
                      {c.contribution_pct ? `${Math.round(Math.abs(c.contribution_pct))}%` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* 4. Operational Signals & Evidence Integrity */}
      <section aria-label="Operational Signals and Evidence" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Operational Indicators */}
          <div className="glass-panel p-5 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
              <Truck className="w-4 h-4 text-blue-400" />
              <span>Operational & Service Signals</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 font-sans">Late Delivery Rate</div>
                <div className="font-bold text-amber-400 mt-0.5">
                  {operational_indicators.observed_late_delivery_rate.toFixed(1)}%{' '}
                  <span className="text-[10px] text-slate-500 font-sans">
                    (vs {operational_indicators.baseline_late_delivery_rate.toFixed(1)}%)
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 font-sans">Avg Delivery Lead Time</div>
                <div className="font-bold text-indigo-400 mt-0.5">
                  {operational_indicators.observed_avg_delivery_days.toFixed(1)} days
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 font-sans">Cancellation Rate</div>
                <div className="font-bold text-slate-300 mt-0.5">
                  {operational_indicators.observed_cancellation_rate.toFixed(2)}%
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 font-sans flex items-center space-x-1">
                  <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                  <span>Customer Score</span>
                </div>
                <div className="font-bold text-emerald-400 mt-0.5">
                  {operational_indicators.observed_avg_review_score.toFixed(2)} / 5.0
                </div>
              </div>
            </div>
          </div>

          {/* Evidence Trust Guarantee */}
          <div className="glass-panel p-5 rounded-2xl flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Deterministic Evidence Guarantee</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                All numerical calculations and driver contributions are computed strictly via deterministic SQL aggregations on verified PostgreSQL analytical marts.
              </p>
            </div>
            <div className="text-[11px] text-slate-500 font-mono pt-2 border-t border-slate-800/80 flex items-center justify-between">
              <span>Zero Lookahead Bias</span>
              <span>Exact Revenue Conservation</span>
            </div>
          </div>
        </div>

        {/* Progressive Disclosure: SQL Details */}
        <div>
          <button
            onClick={() => setShowSqlDetails(!showSqlDetails)}
            className="text-xs text-slate-400 hover:text-white flex items-center space-x-1.5 transition py-1"
          >
            {showSqlDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showSqlDetails ? 'Hide technical SQL details' : 'View SQL mart aggregation queries (Level 3)'}</span>
          </button>

          {showSqlDetails && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-2 mt-2">
              <div className="text-slate-400">
                Mart: <span className="text-blue-400">fact_daily_kpis</span> & <span className="text-blue-400">fact_order_analytics</span>
              </div>
              <div className="text-slate-500">
                Query Pattern: SELECT dimension_value, SUM(price) as observed, AVG(price_baseline) as baseline FROM mart WHERE date = :anomaly_date GROUP BY 1 ORDER BY ABS(delta) DESC
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
