import React from 'react';
import { AnomalyDetectionResponse } from '../types/api';
import { formatDisplayDate } from '../services/formatters';
import { AlertTriangle } from 'lucide-react';

interface CurrentInvestigationContextProps {
  anomalyData: AnomalyDetectionResponse | null;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

export const CurrentInvestigationContext: React.FC<CurrentInvestigationContextProps> = ({
  anomalyData,
  selectedDate,
  onSelectDate,
}) => {
  const results = anomalyData?.results || [];
  const detectedAnomalies = results.filter(
    (r) => r.severity === 'critical' || r.severity === 'warning'
  );

  if (detectedAnomalies.length === 0) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span className="text-slate-400 font-medium">
          <strong className="text-white font-semibold">{detectedAnomalies.length} Anomaly Events</strong> Detected in Selected Window:
        </span>
      </div>

      <div className="flex items-center space-x-1.5 overflow-x-auto">
        {detectedAnomalies.map((anom) => {
          const isSelected = anom.date === selectedDate;
          const isCrit = anom.severity === 'critical';
          return (
            <button
              key={anom.date}
              onClick={() => onSelectDate(anom.date)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition flex items-center space-x-1.5 shrink-0 ${
                isSelected
                  ? 'bg-blue-600 text-white font-bold shadow-sm'
                  : isCrit
                  ? 'bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20'
                  : 'bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isCrit ? 'bg-rose-400' : 'bg-amber-400'
                }`}
              />
              <span>{formatDisplayDate(anom.date)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
