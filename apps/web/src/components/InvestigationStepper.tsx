import React from 'react';
import { NavSection } from './Sidebar';
import { ChevronRight, AlertTriangle, Layers, LineChart, Sparkles } from 'lucide-react';
import { formatDisplayDate } from '../services/formatters';

interface InvestigationStepperProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  selectedDate: string;
}

export const InvestigationStepper: React.FC<InvestigationStepperProps> = ({
  activeSection,
  onSelectSection,
  selectedDate,
}) => {
  const steps: { id: NavSection; number: string; label: string; icon: React.ElementType }[] = [
    { id: 'anomalies', number: '01', label: 'What Changed', icon: AlertTriangle },
    { id: 'root-cause', number: '02', label: 'Why It Changed', icon: Layers },
    { id: 'analytics', number: '03', label: 'Evidence & Drivers', icon: LineChart },
    { id: 'ai-memo', number: '04', label: 'Recommendations', icon: Sparkles },
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-2.5 sm:p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center space-x-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Investigation Flow:
        </span>
        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
          {formatDisplayDate(selectedDate)}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = activeSection === step.id;

          return (
            <React.Fragment key={step.id}>
              <button
                onClick={() => onSelectSection(step.id)}
                className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs transition font-medium ${
                  isActive
                    ? 'bg-blue-600 text-white font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <span
                  className={`text-[10px] font-mono font-bold px-1 rounded ${
                    isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {step.number}
                </span>
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden md:inline">{step.label}</span>
              </button>

              {idx < steps.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 hidden sm:inline" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
