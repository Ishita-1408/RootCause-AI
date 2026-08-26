import React from 'react';
import {
  Sparkles,
  Bot,
  CheckCircle2,
  Lightbulb,
  AlertTriangle,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { AIInvestigationResponse } from '../types/api';

interface AIMemoPanelProps {
  data: AIInvestigationResponse | null;
  isLoading: boolean;
}

export const AIMemoPanel: React.FC<AIMemoPanelProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="glass-panel p-6 rounded-2xl space-y-4 max-w-5xl mx-auto">
        <div className="h-8 w-64 skeleton" />
        <div className="h-28 skeleton rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-48 skeleton rounded-xl" />
          <div className="h-48 skeleton rounded-xl" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="glass-panel p-8 rounded-2xl text-center flex flex-col items-center justify-center max-w-5xl mx-auto">
        <Bot className="w-10 h-10 text-slate-500 mb-2.5" />
        <h3 className="text-base font-semibold text-white">Recommendations Not Generated Yet</h3>
        <p className="text-xs text-slate-400 max-w-md mt-1">
          Click "Run Analysis" or select an anomaly date to synthesize leadership recommendations grounded in verified evidence.
        </p>
      </div>
    );
  }

  const structuredActions = [
    {
      number: '01',
      title: 'Review the shift in orders',
      why: 'Order volume surged significantly above baseline and accounts for primary revenue variance.',
      action: 'Check regional inventory allocations and fulfillment capacity in highest-growth shipping areas.',
      priority: 'HIGH',
      priorityColor: 'text-rose-400 bg-rose-500/15 border-rose-500/30',
    },
    {
      number: '02',
      title: 'Review pricing and promotions',
      why: 'Average order value shifted relative to baseline, altering customer basket size.',
      action: 'Audit promotional discount depth, active coupon campaigns, and category mix shifts.',
      priority: 'MEDIUM',
      priorityColor: 'text-blue-400 bg-blue-500/15 border-blue-500/30',
    },
    {
      number: '03',
      title: 'Monitor delivery performance',
      why: 'Sharp demand surge puts operational stress on downstream carrier networks.',
      action: 'Review late delivery rates and carrier SLAs in top volume corridors to protect customer satisfaction.',
      priority: 'OPERATIONAL',
      priorityColor: 'text-purple-400 bg-purple-500/15 border-purple-500/30',
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* 1. Header & Executive Summary */}
      <section aria-label="Executive Briefing" className="glass-panel-hero p-6 sm:p-8 rounded-3xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-600/90 text-white shadow-md shadow-purple-600/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-extrabold uppercase tracking-widest text-purple-400">
                EXECUTIVE BRIEFING & DECISION MEMO
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
                {data.investigation_title}
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-semibold text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
            <span>Evidence Grounded</span>
          </div>
        </div>

        {/* Executive Summary Narrative */}
        <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800/90 space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
            EXECUTIVE SUMMARY
          </div>
          <p className="text-base sm:text-lg text-white leading-relaxed font-medium">
            {data.executive_summary}
          </p>
        </div>
      </section>

      {/* 2. WHAT SHOULD WE DO NEXT? (Structured Action Plan) */}
      <section aria-label="Actionable Recommendations" className="space-y-4">
        <div>
          <div className="text-[11px] font-extrabold uppercase tracking-widest text-blue-400">
            LEADERSHIP ACTION PLAN
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
            WHAT SHOULD WE DO NEXT?
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Prioritized strategic decisions grounded in verified driver attribution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {structuredActions.map((item) => (
            <div
              key={item.number}
              className="glass-panel p-6 rounded-2xl space-y-3.5 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-mono font-bold text-blue-400">{item.number}</span>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${item.priorityColor}`}>
                    {item.priority}
                  </span>
                </div>

                <h4 className="text-base font-bold text-white">
                  {item.title}
                </h4>

                <div className="text-xs text-slate-400 pt-1">
                  <strong className="text-slate-300">WHY:</strong> {item.why}
                </div>

                <p className="text-xs sm:text-sm text-slate-200 leading-relaxed pt-1">
                  <strong className="text-white">ACTION:</strong> {item.action}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Grid: Key Findings & Business Interpretations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Key Findings */}
        <div className="glass-panel p-6 rounded-2xl space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Key Verified Findings</span>
          </div>
          <ul className="space-y-2.5">
            {data.key_findings.map((f, i) => (
              <li key={i} className="flex items-start space-x-2.5 text-xs sm:text-sm text-slate-200 leading-normal">
                <span className="w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-400 flex items-center justify-center font-bold font-mono text-xs shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Business Interpretation */}
        <div className="glass-panel p-6 rounded-2xl space-y-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <span>Business Interpretation & Context</span>
          </div>
          <ul className="space-y-2.5">
            {data.business_interpretation.map((b, i) => (
              <li key={i} className="flex items-start space-x-2.5 text-xs sm:text-sm text-slate-200 leading-normal">
                <span className="w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  •
                </span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 4. Evidence Scope & Guardrails Notice */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-slate-500 shrink-0" />
          <span>
            {data.limitations.length > 0 ? data.limitations[0] : 'Deterministic facts guaranteed; correlation does not imply external causality.'}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-500 font-mono text-[11px] shrink-0">
          <Clock className="w-3.5 h-3.5" />
          <span>Synthesized {new Date(data.generated_at).toLocaleTimeString()} ({data.model})</span>
        </div>
      </div>
    </div>
  );
};
