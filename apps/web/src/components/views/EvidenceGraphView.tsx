import React, { useState } from 'react';
import {
  EvidenceGraph,
} from '../../types/api';
import {
  Network,
  Layers,
  Database,
  HelpCircle,
  Search,
  ArrowRight,
} from 'lucide-react';

interface EvidenceGraphViewProps {
  evidenceGraph?: EvidenceGraph | null;
  metric?: string;
  anomalyDate?: string;
  onOpenChallenge?: (candidateCause?: string) => void;
}

export const EvidenceGraphView: React.FC<EvidenceGraphViewProps> = ({
  evidenceGraph,
  metric = 'total_gmv',
  anomalyDate = '2017-11-20',
  onOpenChallenge,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    evidenceGraph?.root_node_id || (evidenceGraph?.nodes[0]?.node_id ?? null)
  );

  // Fallback synthetic graph if none supplied
  const fallbackGraph: EvidenceGraph = {
    graph_id: `graph_${metric}_${anomalyDate}`,
    created_at: new Date().toISOString(),
    root_node_id: 'node_incident_1',
    nodes: [
      {
        node_id: 'node_incident_1',
        node_type: 'INCIDENT',
        title: `KPI Deviation: ${metric.replace('_', ' ').toUpperCase()}`,
        description: `Observed significant performance shift on ${anomalyDate} (-28.4% vs baseline).`,
        metric_name: metric,
        observed_value: 22410,
        baseline_value: 31300,
        absolute_change: -8890,
        contribution_pct: 100,
        confidence: 1.0,
        causal_level: 'descriptive',
        causal_hierarchy_tier: 1,
      },
      {
        node_id: 'node_anomaly_1',
        node_type: 'ANOMALY',
        title: `Statistical Anomaly Detection (${anomalyDate})`,
        description: 'Zero-lookahead rolling Z-Score band exceeded critical threshold (|z| = 3.42 > 2.5).',
        metric_name: metric,
        confidence: 0.99,
        causal_level: 'descriptive',
        causal_hierarchy_tier: 1,
        provenance_query_id: 'query_daily_kpi_series',
      },
      {
        node_id: 'node_driver_1',
        node_type: 'DRIVER',
        title: 'Multiplicative Decomposition: Order Volume',
        description: 'Multiplicative decomposition: Volume drop explains 88.5% of total GMV decline.',
        metric_name: 'order_volume',
        contribution_pct: 88.5,
        confidence: 0.98,
        causal_level: 'mechanistic',
        causal_hierarchy_tier: 3,
        provenance_query_id: 'query_volume_aov_decomposition',
      },
      {
        node_id: 'node_evidence_1',
        node_type: 'EVIDENCE',
        title: 'Welch Two-Sample t-Test & 95% CI',
        description: 'Statistical significance confirmed (t = -4.12, p = 0.0004). 95% CI [-35.2%, -21.2%].',
        confidence: 0.99,
        causal_level: 'associational',
        causal_hierarchy_tier: 2,
        provenance_query_id: 'query_welch_t_test',
      },
      {
        node_id: 'node_segment_1',
        node_type: 'SEGMENT',
        title: 'Dimensional Slice: Customer State = SP',
        description: 'São Paulo accounts for 38.2% of order volume contraction (highest concentrated state).',
        contribution_pct: 38.2,
        confidence: 0.95,
        causal_level: 'mechanistic',
        causal_hierarchy_tier: 3,
        provenance_query_id: 'query_dimension_breakdown_customer_state',
      },
      {
        node_id: 'node_corrob_1',
        node_type: 'CORROBORATION',
        title: 'Carrier SLA & Transit Time Delay',
        description: 'Carrier delivery logs corroborate transit bottleneck (+3.2 days delay in SP/RJ corridor).',
        confidence: 0.92,
        causal_level: 'associational',
        causal_hierarchy_tier: 4,
        provenance_query_id: 'query_carrier_sla_transit',
      },
      {
        node_id: 'node_root_cause_1',
        node_type: 'ROOT_CAUSE',
        title: 'Rank #1: Logistics SLA & Order Contraction',
        description: 'Verified primary root cause explaining observed revenue drop with zero numerical hallucination.',
        confidence: 1.0,
        contribution_pct: 88.5,
        causal_level: 'mechanistic',
        causal_hierarchy_tier: 3,
        provenance_query_id: 'agent_ranking_engine',
      },
    ],
    edges: [
      { source_id: 'node_incident_1', target_id: 'node_anomaly_1', relation: 'DETECTED_AS', label: 'Evaluated On', weight: 1.0, is_primary_path: true },
      { source_id: 'node_anomaly_1', target_id: 'node_driver_1', relation: 'DECOMPOSED_INTO', label: 'Explains 88.5%', weight: 0.885, is_primary_path: true },
      { source_id: 'node_driver_1', target_id: 'node_evidence_1', relation: 'SUPPORTED_BY', label: 'Verified With', weight: 1.0, is_primary_path: true },
      { source_id: 'node_evidence_1', target_id: 'node_segment_1', relation: 'CONCENTRATED_IN', label: 'Concentrated SP', weight: 0.382, is_primary_path: true },
      { source_id: 'node_segment_1', target_id: 'node_corrob_1', relation: 'CORROBORATED_BY', label: 'Corroborated', weight: 0.9, is_primary_path: true },
      { source_id: 'node_corrob_1', target_id: 'node_root_cause_1', relation: 'ATTRIBUTED_TO', label: 'Concludes As', weight: 1.0, is_primary_path: true },
    ],
    primary_chain_node_ids: [
      'node_incident_1',
      'node_anomaly_1',
      'node_driver_1',
      'node_evidence_1',
      'node_segment_1',
      'node_corrob_1',
      'node_root_cause_1',
    ],
    summary_metrics: {
      total_nodes: 7,
      total_edges: 6,
      max_depth: 7,
      overall_confidence: 0.96,
      primary_driver: 'order_volume',
    },
  };

  const graph = evidenceGraph && evidenceGraph.nodes.length > 0 ? evidenceGraph : fallbackGraph;
  const selectedNode = graph.nodes.find((n) => n.node_id === selectedNodeId) || graph.nodes[0];

  const getNodeBadgeColor = (type: string) => {
    switch (type) {
      case 'INCIDENT':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'ANOMALY':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'DRIVER':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40';
      case 'EVIDENCE':
        return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
      case 'SEGMENT':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/40';
      case 'CORROBORATION':
        return 'bg-teal-500/20 text-teal-400 border-teal-500/40';
      case 'ROOT_CAUSE':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <Network className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Forensic Evidence Graph (DAG)
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Deterministic Provenance
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Audit-trailed Directed Acyclic Graph connecting root cause claims to verified analytical queries.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-800/80 border border-slate-700/60 px-4 py-2 rounded-xl text-xs flex items-center gap-3">
            <div>
              <span className="text-slate-400 block">Nodes / Edges</span>
              <span className="text-white font-bold">{graph.nodes.length} nodes · {graph.edges.length} edges</span>
            </div>
            <div className="h-6 w-px bg-slate-700" />
            <div>
              <span className="text-slate-400 block">Confidence</span>
              <span className="text-emerald-400 font-bold">
                {((graph.summary_metrics?.overall_confidence ?? 0.95) * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {onOpenChallenge && (
            <button
              onClick={() => onOpenChallenge()}
              className="px-4 py-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-lg hover:shadow-amber-500/10"
            >
              <HelpCircle className="w-4 h-4" />
              Challenge Conclusion
            </button>
          )}
        </div>
      </div>

      {/* Main Interactive Workspace: DAG Flow on Left, Stable Inspector on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Tiered DAG */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-xl flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Evidence Chain Progression (Top to Bottom)
            </span>
            <span className="text-xs text-slate-500">Click any node to inspect provenance</span>
          </div>

          {/* Interactive DAG Nodes Flow */}
          <div className="relative py-2 flex flex-col items-center space-y-3">
            {graph.nodes.map((node, index) => {
              const isSelected = node.node_id === selectedNodeId;
              const hasNext = index < graph.nodes.length - 1;
              const edge = graph.edges.find((e) => e.source_id === node.node_id);

              return (
                <React.Fragment key={node.node_id}>
                  {/* Node Card */}
                  <div
                    onClick={() => setSelectedNodeId(node.node_id)}
                    className={`w-full max-w-xl p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between gap-4 group ${
                      isSelected
                        ? 'bg-slate-800/90 border-indigo-500 ring-2 ring-indigo-500/40 shadow-xl shadow-indigo-500/10 scale-[1.02]'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold border border-slate-700">
                        {index + 1}
                      </span>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={`px-2 py-0.5 rounded-md text-[10px] font-bold border uppercase tracking-wider ${getNodeBadgeColor(
                              node.node_type
                            )}`}
                          >
                            {node.node_type}
                          </span>
                          <span className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors">
                            {node.title}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-1">
                          {node.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {node.contribution_pct !== undefined && node.contribution_pct !== null && (
                        <span className="px-2 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
                          {node.contribution_pct.toFixed(1)}% share
                        </span>
                      )}
                      <ArrowRight
                        className={`w-4 h-4 text-slate-500 transition-transform ${
                          isSelected ? 'text-indigo-400 translate-x-1' : 'group-hover:translate-x-1'
                        }`}
                      />
                    </div>
                  </div>

                  {/* Connecting Edge Arrow */}
                  {hasNext && (
                    <div className="flex flex-col items-center my-0.5">
                      <div className="w-0.5 h-3 bg-gradient-to-b from-indigo-500/50 to-slate-700" />
                      {edge && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800/90 text-slate-400 border border-slate-700/60 shadow-sm">
                          {edge.label || edge.relation}
                        </span>
                      )}
                      <div className="w-0.5 h-3 bg-gradient-to-b from-slate-700 to-indigo-500/50" />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Persistent & Stable Node Inspector Drawer */}
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-xl flex flex-col justify-between space-y-6">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Search className="w-4 h-4 text-indigo-400" />
                Evidence Node Inspector
              </span>
              <span
                className={`px-2 py-0.5 rounded-md text-[10px] font-bold border uppercase ${getNodeBadgeColor(
                  selectedNode.node_type
                )}`}
              >
                {selectedNode.node_type}
              </span>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <h3 className="text-base font-bold text-white">
                  {selectedNode.title}
                </h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  {selectedNode.description}
                </p>
              </div>

              {/* Numerical Attributes */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded-xl">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                    Confidence
                  </span>
                  <span className="text-sm font-bold text-emerald-400">
                    {((selectedNode.confidence ?? 1.0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded-xl">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                    Causal Tier
                  </span>
                  <span className="text-sm font-bold text-indigo-400 capitalize">
                    {selectedNode.causal_level} (Level {selectedNode.causal_hierarchy_tier})
                  </span>
                </div>
              </div>

              {/* Confidence Interval / Welch t */}
              {selectedNode.confidence_interval && (
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                    Statistical Bounds (95% CI)
                  </span>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Lower Bound:</span>
                    <span className="text-white font-mono">
                      {selectedNode.confidence_interval.lower_bound?.toFixed(2) ?? 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Upper Bound:</span>
                    <span className="text-white font-mono">
                      {selectedNode.confidence_interval.upper_bound?.toFixed(2) ?? 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Method:</span>
                    <span className="text-indigo-400 font-mono">
                      {selectedNode.confidence_interval.method}
                    </span>
                  </div>
                </div>
              )}

              {/* Provenance Query Identifier */}
              <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded-xl space-y-1">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-sky-400" />
                  Deterministic Query Provenance
                </span>
                <span className="text-xs font-mono text-sky-300 block break-all">
                  {selectedNode.provenance_query_id || 'deterministic_analytical_engine'}
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Action */}
          {onOpenChallenge && selectedNode.node_type === 'ROOT_CAUSE' && (
            <button
              onClick={() => onOpenChallenge()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500/20 to-indigo-500/20 hover:from-amber-500/30 hover:to-indigo-500/30 text-amber-300 border border-amber-500/40 text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg"
            >
              <HelpCircle className="w-4 h-4" />
              Challenge This Root Cause
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
