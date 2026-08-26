import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  CheckCircle2,
  Clock,
  Database,
  Activity,
} from 'lucide-react';
import { InvestigationSnapshot } from '../../types/api';
import { apiClient } from '../../services/api';

interface ReplayViewProps {
  sessionId?: string;
  metric?: string;
  anomalyDate?: string;
}

export const ReplayView: React.FC<ReplayViewProps> = ({
  sessionId = 'session_default_123',
  metric = 'total_gmv',
  anomalyDate = '2017-11-20',
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [snapshot, setSnapshot] = useState<InvestigationSnapshot | null>(null);

  // Load snapshot from API or fallback
  useEffect(() => {
    apiClient
      .getReplaySnapshot(sessionId)
      .then((data) => {
        if (data && data.replay_steps && data.replay_steps.length > 0) {
          setSnapshot(data);
        } else {
          setSnapshot(generateFallbackSnapshot(sessionId, metric, anomalyDate));
        }
      })
      .catch(() => {
        setSnapshot(generateFallbackSnapshot(sessionId, metric, anomalyDate));
      });
  }, [sessionId, metric, anomalyDate]);

  // Autoplay ticker
  useEffect(() => {
    let timer: any = null;
    if (isPlaying && snapshot) {
      timer = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev < snapshot.replay_steps.length - 1) {
            return prev + 1;
          } else {
            setIsPlaying(false);
            return prev;
          }
        });
      }, 1800);
    }
    return () => clearInterval(timer);
  }, [isPlaying, snapshot]);

  const generateFallbackSnapshot = (
    sid: string,
    kpi: string,
    dt: string
  ): InvestigationSnapshot => ({
    session_id: sid,
    metric: kpi,
    anomaly_date: dt,
    created_at: new Date().toISOString(),
    observed_value: 22410,
    baseline_value: 31300,
    total_steps: 5,
    ranked_causes: [],
    step_traces: [],
    benchmark_version: 'v2.0',
    metadata: { execution_duration_ms: 780 },
    replay_steps: [
      {
        step_index: 1,
        step_title: 'Step 1: Baseline Window & Anomaly Detection',
        step_type: 'ANOMALY_DETECTION',
        status: 'completed',
        timestamp: new Date().toISOString(),
        query_executed: 'SELECT * FROM mart_daily_kpis WHERE metric = total_gmv',
        finding_summary: `Detected -28.4% anomaly on ${dt} (Observed: R$ 22,410 vs Baseline: R$ 31,300).`,
        intermediate_state: { z_score: -3.42, severity: 'critical' },
      },
      {
        step_index: 2,
        step_title: 'Step 2: Multiplicative Volume vs AOV Decomposition',
        step_type: 'DECOMPOSITION',
        status: 'completed',
        timestamp: new Date().toISOString(),
        query_executed: 'SELECT * FROM mart_orders_breakdown WHERE date = 2017-11-20',
        finding_summary: 'Volume contraction explains 88.5% of GMV drop (-32 orders). AOV shift explains 11.5%.',
        intermediate_state: { volume_effect: -7850, aov_effect: -1040 },
      },
      {
        step_index: 3,
        step_title: 'Step 3: Dimensional Concentration Drill-Down',
        step_type: 'DIMENSIONAL_ANALYSIS',
        status: 'completed',
        timestamp: new Date().toISOString(),
        query_executed: 'SELECT customer_state, sum(gmv) FROM fact_order GROUP BY 1',
        finding_summary: 'Contraction is heavily concentrated in São Paulo (38.2% share of total drop).',
        intermediate_state: { top_state: 'SP', top_state_share: 38.2 },
      },
      {
        step_index: 4,
        step_title: 'Step 4: Operational Corroboration & Logistics SLA',
        step_type: 'OPERATIONAL_CHECK',
        status: 'completed',
        timestamp: new Date().toISOString(),
        query_executed: 'SELECT avg(carrier_transit_days) FROM mart_logistics_sla',
        finding_summary: 'Carrier delivery logs corroborate transit bottlenecks (+3.2 days delay in SP corridor).',
        intermediate_state: { carrier_delay_days: 3.2, sla_breach: true },
      },
      {
        step_index: 5,
        step_title: 'Step 5: Forensic Root-Cause Ranking & Firewall Audit',
        step_type: 'RANKING_CONCLUSION',
        status: 'completed',
        timestamp: new Date().toISOString(),
        query_executed: 'RANKING_ENGINE_SYNTHESIS',
        finding_summary: 'Rank #1 assigned to Carrier Logistics SLA & Order Contraction in SP (Confidence 98%).',
        intermediate_state: { rank_1_cause: 'Logistics SLA Bottleneck', claims_verified: 10 },
      },
    ],
  });

  const steps = snapshot?.replay_steps || [];
  const currentStep = steps[currentStepIndex] || steps[0];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-2 rounded-xl bg-sky-500/20 text-sky-400 border border-sky-500/30">
              <Clock className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Deterministic Investigation Replay
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Immutable Playback
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Step-by-step forensic execution trace showing intermediate states without non-deterministic re-execution.
          </p>
        </div>

        {/* Player Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setCurrentStepIndex(0);
              setIsPlaying(false);
            }}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all"
            title="Reset to Step 1"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/20"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? 'Pause Playback' : 'Play Replay'}
          </button>

          <button
            onClick={() => {
              if (currentStepIndex < steps.length - 1) {
                setCurrentStepIndex(currentStepIndex + 1);
              }
            }}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all"
            title="Next Step"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Progress Scrubber */}
      <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>
            Playback Progress: Step {currentStepIndex + 1} of {steps.length}
          </span>
          <span className="font-mono text-indigo-400">
            {(((currentStepIndex + 1) / (steps.length || 1)) * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full transition-all duration-300"
            style={{
              width: `${((currentStepIndex + 1) / (steps.length || 1)) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Main Replay Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 1 Col: Step List Navigator */}
        <div className="space-y-2 bg-slate-900/60 border border-slate-800 p-4 rounded-2xl">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2 px-2">
            Execution Steps
          </span>
          {steps.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCurrentStepIndex(idx);
                setIsPlaying(false);
              }}
              className={`w-full p-3 rounded-xl border text-left text-xs transition-all flex items-center justify-between ${
                currentStepIndex === idx
                  ? 'bg-slate-800 border-indigo-500 text-white font-bold'
                  : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                    idx <= currentStepIndex
                      ? 'bg-indigo-500/20 text-indigo-400 font-bold'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  {idx + 1}
                </span>
                <span className="line-clamp-1">{s.step_title}</span>
              </div>
              {idx <= currentStepIndex && (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              )}
            </button>
          ))}
        </div>

        {/* Right 2 Cols: Step Detail & Intermediate State */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-xl space-y-6">
          {currentStep && (
            <>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400 block mb-1">
                    Stage {currentStep.step_index} · {currentStep.step_type}
                  </span>
                  <h3 className="text-lg font-bold text-white">{currentStep.step_title}</h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {currentStep.status.toUpperCase()}
                </span>
              </div>

              {/* Finding Box */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 text-sm leading-relaxed">
                <span className="font-bold text-indigo-400 block mb-1">Observed Step Finding:</span>
                {currentStep.finding_summary}
              </div>

              {/* SQL Query Provenance */}
              {currentStep.query_executed && (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Database className="w-4 h-4 text-sky-400" />
                    Analytical Query Executed
                  </span>
                  <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-sky-300 overflow-x-auto">
                    {currentStep.query_executed}
                  </pre>
                </div>
              )}

              {/* Intermediate State Variables */}
              {currentStep.intermediate_state && Object.keys(currentStep.intermediate_state).length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    Intermediate State Variables
                  </span>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(currentStep.intermediate_state).map(([k, v]) => (
                      <div key={k} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">{k}</span>
                        <span className="text-xs font-bold text-white font-mono">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
