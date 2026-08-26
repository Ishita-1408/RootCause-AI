import React, { useState } from 'react';
import {
  AlertCircle,
  MousePointerClick,
  ArrowRight,
} from 'lucide-react';
import { AnomalyDetectionResponse, AnomalyResult, MetricType } from '../types/api';
import { formatMetricValue, formatDisplayDate, getMetricLabel } from '../services/formatters';

interface AnomalyTimelineProps {
  data: AnomalyDetectionResponse | null;
  selectedDate: string;
  onSelectDate: (date: string) => void;
  onNavigateToRootCause?: () => void;
  metric: MetricType;
  isLoading: boolean;
}

export const AnomalyTimeline: React.FC<AnomalyTimelineProps> = ({
  data,
  selectedDate,
  onSelectDate,
  onNavigateToRootCause,
  metric,
  isLoading,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<AnomalyResult | null>(null);

  const results = data?.results || [];
  const detectedAnomalies = results.filter(
    (r) => r.severity === 'critical' || r.severity === 'warning'
  );
  const criticalCount = results.filter((r) => r.severity === 'critical').length;
  const warningCount = results.filter((r) => r.severity === 'warning').length;

  const currentAnomaly = results.find((r) => r.date === selectedDate) || results[0];
  const metricLabel = getMetricLabel(metric);

  // Compute SVG chart coordinates
  const validPoints = results.filter((r) => r.observed_value !== null && r.observed_value !== undefined);
  const maxVal = Math.max(...validPoints.map((r) => r.observed_value || 0), 1);
  const minVal = Math.min(...validPoints.map((r) => r.observed_value || 0), 0);
  const range = maxVal - minVal || 1;

  const width = 840;
  const height = 260;
  const padding = { top: 30, right: 30, bottom: 40, left: 65 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const getX = (index: number) => {
    if (results.length <= 1) return padding.left;
    return padding.left + (index / (results.length - 1)) * chartW;
  };

  const getY = (val: number | null) => {
    if (val === null || val === undefined) return padding.top + chartH;
    const normalized = (val - minVal) / range;
    return padding.top + chartH - normalized * chartH;
  };

  // Generate SVG paths
  const observedPath = results
    .map((r, i) => {
      const x = getX(i);
      const y = getY(r.observed_value);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');

  const baselinePath = results
    .filter((r) => r.baseline_mean !== null)
    .map((r, i) => {
      const idx = results.indexOf(r);
      const x = getX(idx);
      const y = getY(r.baseline_mean);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');

  // Compute stats for current anomaly card
  const obsVal = currentAnomaly?.observed_value ?? 0;
  const baseMean = currentAnomaly?.baseline_mean ?? 0;
  const delta = obsVal - baseMean;
  const pctShift = baseMean > 0 ? ((obsVal - baseMean) / baseMean) * 100 : 0;
  const isIncrease = delta >= 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto py-2">
      {/* 1. Header: WHAT CHANGED? */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2">
        <div>
          <div className="text-[11px] font-extrabold uppercase tracking-widest text-amber-400">
            WHAT CHANGED?
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mt-0.5">
            {detectedAnomalies.length > 0
              ? `Found ${detectedAnomalies.length} unusual anomalies during this period.`
              : `All daily observations are within the expected normal range.`}
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Comparing daily <strong className="text-slate-200">{metricLabel.toLowerCase()}</strong> against its 7-day rolling historical baseline.
          </p>
        </div>

        {/* Severity Count Summary */}
        <div className="bg-slate-900/90 px-4 py-2 rounded-2xl border border-slate-800 text-xs font-semibold flex items-center space-x-2 shrink-0">
          <span className="font-mono text-white">{detectedAnomalies.length} Anomalies</span>
          <span className="text-slate-600">•</span>
          <span className="text-rose-400 font-bold">{criticalCount} Critical</span>
          <span className="text-slate-600">•</span>
          <span className="text-amber-400 font-bold">{warningCount} Warning</span>
        </div>
      </div>

      {/* 2. Interactive Focus Card: WHAT HAPPENED? / WHY IT MATTERS? / INVESTIGATE WHY */}
      {currentAnomaly && (
        <div className="glass-panel-hero p-6 rounded-2xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2.5">
              <span
                className={`w-3 h-3 rounded-full shrink-0 ${currentAnomaly.severity === 'critical'
                  ? 'bg-rose-500 animate-pulse'
                  : currentAnomaly.severity === 'warning'
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                  }`}
              />
              <span className="text-base sm:text-lg font-bold text-white font-mono">
                {formatDisplayDate(currentAnomaly.date)}
              </span>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${currentAnomaly.severity === 'critical'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : currentAnomaly.severity === 'warning'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}
              >
                {currentAnomaly.severity} Event
              </span>
            </div>

            {onNavigateToRootCause && (
              <button
                onClick={onNavigateToRootCause}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs sm:text-sm transition flex items-center space-x-2 shadow-md shadow-blue-600/30 shrink-0"
              >
                <span>INVESTIGATE WHY</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-1">
            {/* What Happened Column */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">
                WHAT HAPPENED?
              </span>
              <p className="text-sm text-slate-200 leading-relaxed font-medium">
                {metricLabel} was{' '}
                <strong className="text-white font-mono font-bold">
                  {formatMetricValue(obsVal, metric)}
                </strong>
                , which is{' '}
                <span className={`font-bold ${isIncrease ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isIncrease ? '+' : ''}{pctShift.toFixed(1)}% ({isIncrease ? '+' : ''}{formatMetricValue(delta, metric)})
                </span>{' '}
                relative to the expected baseline of{' '}
                <span className="text-slate-300 font-mono">
                  {formatMetricValue(baseMean, metric)}
                </span>
                .
              </p>
            </div>

            {/* Why It Matters Column */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                WHY IT MATTERS?
              </span>
              <p className="text-sm text-slate-300 leading-relaxed">
                {currentAnomaly.z_score !== null ? (
                  <>
                    Statistical Z-score was{' '}
                    <strong className="text-white font-mono font-bold">
                      {currentAnomaly.z_score > 0 ? '+' : ''}{currentAnomaly.z_score.toFixed(2)}σ
                    </strong>{' '}
                    (well beyond the 2.0 standard deviation threshold). This confirms an intentional demand or operational surge, not random noise.
                  </>
                ) : (
                  'Variance exceeds normal confidence intervals.'
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 3. Hero Interactive Timeline Chart */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Daily Trend & Rolling Baseline
          </h3>
          <div className="flex items-center space-x-1.5 text-xs text-slate-400">
            <MousePointerClick className="w-3.5 h-3.5 text-blue-400" />
            <span>Click any node to focus date</span>
          </div>
        </div>

        <div className="relative">
          {isLoading ? (
            <div className="h-64 flex items-center justify-center skeleton rounded-xl">
              <span className="text-xs text-slate-400">Loading daily KPI time-series...</span>
            </div>
          ) : results.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl">
              <AlertCircle className="w-8 h-8 text-slate-500 mb-2" />
              <p className="text-sm font-medium text-slate-400">No time-series observations in this date range</p>
            </div>
          ) : (
            <div className="w-full">
              <svg
                viewBox={`0 0 ${width} ${height}`}
                className="w-full h-auto max-h-72 select-none"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Horizontal Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                  const y = padding.top + chartH * (1 - pct);
                  const val = minVal + range * pct;
                  return (
                    <g key={i}>
                      <line
                        x1={padding.left}
                        y1={y}
                        x2={width - padding.right}
                        y2={y}
                        stroke="#1e293b"
                        strokeDasharray="4 4"
                        opacity="0.6"
                      />
                      <text
                        x={padding.left - 12}
                        y={y + 4}
                        fill="#64748b"
                        fontSize="10"
                        textAnchor="end"
                        fontFamily="var(--font-mono)"
                      >
                        {val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val.toFixed(0)}
                      </text>
                    </g>
                  );
                })}

                {/* Baseline Mean Curve */}
                {baselinePath && (
                  <path
                    d={baselinePath}
                    fill="none"
                    stroke="#818cf8"
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                    opacity="0.75"
                  />
                )}

                {/* Observed Line */}
                {observedPath && (
                  <path
                    d={observedPath}
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Data Points */}
                {results.map((r, i) => {
                  const x = getX(i);
                  const y = getY(r.observed_value);
                  const isSelected = r.date === selectedDate;
                  const isCritical = r.severity === 'critical';
                  const isWarning = r.severity === 'warning';

                  let fillColor = '#3b82f6';
                  let radius = 4;

                  if (isCritical) {
                    fillColor = '#ef4444';
                    radius = isSelected ? 8 : 6;
                  } else if (isWarning) {
                    fillColor = '#f59e0b';
                    radius = isSelected ? 7 : 5;
                  } else if (isSelected) {
                    fillColor = '#60a5fa';
                    radius = 5.5;
                  }

                  return (
                    <g
                      key={i}
                      className="cursor-pointer transition-transform hover:scale-125"
                      onClick={() => onSelectDate(r.date)}
                      onMouseEnter={() => setHoveredPoint(r)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    >
                      {isSelected && (
                        <circle
                          cx={x}
                          cy={y}
                          r={radius + 4}
                          fill="none"
                          stroke={fillColor}
                          strokeWidth="2"
                          opacity="0.8"
                        />
                      )}
                      <circle
                        cx={x}
                        cy={y}
                        r={radius}
                        fill={fillColor}
                        stroke="#090d16"
                        strokeWidth="1.5"
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Chart Legend */}
              <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/60 gap-3">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center space-x-1.5">
                    <span className="w-3 h-0.5 bg-blue-500 inline-block rounded" />
                    <span className="text-slate-300">Observed Value</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-3 h-0.5 border-t border-indigo-400 border-dashed inline-block" />
                    <span>7-Day Expected Baseline</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                    <span>Warning (|z| ≥ 2.0)</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                    <span>Critical Anomaly</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Hover Tooltip */}
          {hoveredPoint && (
            <div className="absolute top-2 right-4 glass-panel p-3.5 rounded-xl shadow-xl text-xs z-20 border border-blue-500/30 font-sans">
              <div className="font-bold text-white mb-1.5 flex items-center justify-between gap-4">
                <span>{formatDisplayDate(hoveredPoint.date)}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${hoveredPoint.severity === 'critical'
                    ? 'bg-rose-500/20 text-rose-400'
                    : hoveredPoint.severity === 'warning'
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'text-slate-400'
                    }`}
                >
                  {hoveredPoint.severity}
                </span>
              </div>
              <div className="space-y-0.5 text-slate-300 font-mono">
                <div>Observed: {formatMetricValue(hoveredPoint.observed_value, metric)}</div>
                <div>Expected: {formatMetricValue(hoveredPoint.baseline_mean, metric)}</div>
                {hoveredPoint.z_score && <div>Z-Score: {hoveredPoint.z_score.toFixed(2)}σ</div>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
