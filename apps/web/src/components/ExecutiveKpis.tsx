import React from 'react';
import { DollarSign, ShoppingBag, CreditCard, Clock, Star, AlertTriangle } from 'lucide-react';
import { AnomalyDetectionResponse } from '../types/api';
import { formatMetricValue } from '../services/formatters';

interface ExecutiveKpisProps {
  anomalyData: AnomalyDetectionResponse | null;
  isLoading: boolean;
}

export const ExecutiveKpis: React.FC<ExecutiveKpisProps> = ({ anomalyData, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="glass-panel p-4 h-24 skeleton" />
        ))}
      </div>
    );
  }

  const results = anomalyData?.results || [];
  const latestResult = results.length > 0 ? results[results.length - 1] : null;
  const currentMetric = anomalyData?.metric || 'total_gmv';

  // Calculate totals and averages over the period
  const totalObservations = results.length;
  const anomaliesCount = anomalyData?.anomalies_count || 0;
  const criticalCount = results.filter((r) => r.severity === 'critical').length;
  const warningCount = results.filter((r) => r.severity === 'warning').length;

  const cards = [
    {
      title: 'Target Metric',
      value: currentMetric.replace(/_/g, ' ').toUpperCase(),
      sub: `${totalObservations} Days Evaluated`,
      icon: DollarSign,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20',
    },
    {
      title: 'Latest Observation',
      value:
        latestResult?.observed_value !== null && latestResult?.observed_value !== undefined
          ? formatMetricValue(latestResult.observed_value, currentMetric)
          : 'N/A',
      sub: latestResult ? `Date: ${latestResult.date}` : 'No Data',
      icon: ShoppingBag,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-500/20',
    },
    {
      title: 'Active Anomalies',
      value: anomaliesCount.toString(),
      sub: `${criticalCount} Critical | ${warningCount} Warning`,
      icon: AlertTriangle,
      color: anomaliesCount > 0 ? 'text-rose-400' : 'text-emerald-400',
      bgColor: anomaliesCount > 0 ? 'bg-rose-500/10' : 'bg-emerald-500/10',
      borderColor: anomaliesCount > 0 ? 'border-rose-500/20' : 'border-emerald-500/20',
    },
    {
      title: 'Rolling Baseline',
      value: `${anomalyData?.window || 7} Days`,
      sub: 'Lagged Shift (Zero Leakage)',
      icon: Clock,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/20',
    },
    {
      title: 'Z-Score Sensitivity',
      value: `|z| ≥ ${anomalyData?.z_threshold || 2.0}`,
      sub: 'Standard Deviation Threshold',
      icon: CreditCard,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20',
    },
    {
      title: 'Engine Status',
      value: 'Deterministic',
      sub: '100% Verifiable Math',
      icon: Star,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
      {cards.map((c, idx) => {
        const Icon = c.icon;
        return (
          <div
            key={idx}
            className={`glass-panel p-3.5 sm:p-4 rounded-xl border ${c.borderColor} hover:scale-[1.01] transition-transform`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">
                {c.title}
              </span>
              <div className={`p-1.5 rounded-lg ${c.bgColor}`}>
                <Icon className={`w-3.5 h-3.5 ${c.color}`} />
              </div>
            </div>
            <div className="text-sm sm:text-base font-bold text-white tracking-tight truncate">
              {c.value}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 truncate">{c.sub}</div>
          </div>
        );
      })}
    </div>
  );
};

