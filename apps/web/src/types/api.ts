/**
 * RootCause AI — TypeScript API Contracts (matching FastAPI OpenAPI Schema)
 */

export type MetricType =
  | 'total_gmv'
  | 'orders_count'
  | 'average_order_value'
  | 'late_delivery_rate_pct'
  | 'avg_review_score';

export type AnomalySeverity = 'normal' | 'warning' | 'critical';
export type DirectionType = 'increase' | 'decrease' | 'normal' | 'unchanged';

export interface AnomalyResult {
  date: string;
  metric: string;
  observed_value: number | null;
  baseline_mean: number | null;
  baseline_std: number | null;
  z_score: number | null;
  severity: AnomalySeverity;
  is_anomaly: boolean;
  direction: DirectionType;
}

export interface AnomalyDetectionRequest {
  metric: MetricType;
  start_date: string;
  end_date: string;
  product_category?: string | null;
  window?: number;
  z_threshold?: number;
  minimum_history?: number;
}

export interface AnomalyDetectionResponse {
  metric: string;
  product_category: string | null;
  start_date: string;
  end_date: string;
  window: number;
  z_threshold: number;
  minimum_history: number;
  total_observations: number;
  anomalies_count: number;
  results: AnomalyResult[];
}

export interface DimensionContributor {
  dimension: string;
  dimension_value: string;
  observed_value: number;
  baseline_value: number;
  absolute_change: number;
  percentage_change: number | null;
  contribution_pct: number | null;
  direction: DirectionType;
  rank: number;
}

export interface VolumeValueDecomposition {
  observed_orders: number;
  baseline_orders: number;
  observed_aov: number;
  baseline_aov: number;
  volume_effect: number;
  aov_effect: number;
  interaction_effect: number;
  total_change: number;
  volume_contribution_pct: number | null;
  aov_contribution_pct: number | null;
  interaction_contribution_pct: number | null;
}

export interface OperationalIndicators {
  observed_late_delivery_rate: number;
  baseline_late_delivery_rate: number;
  late_delivery_rate_change: number;
  observed_avg_delivery_days: number;
  baseline_avg_delivery_days: number;
  avg_delivery_days_change: number;
  observed_cancellation_rate: number;
  baseline_cancellation_rate: number;
  cancellation_rate_change: number;
  observed_avg_review_score: number;
  baseline_avg_review_score: number;
  avg_review_score_change: number;
}

export interface AnomalySummary {
  metric: string;
  anomaly_date: string;
  baseline_start_date: string;
  baseline_end_date: string;
  observed_value: number;
  baseline_value: number;
  absolute_change: number;
  percentage_change: number | null;
  direction: DirectionType;
}

export interface RootCauseInvestigationRequest {
  metric: MetricType;
  anomaly_date: string;
  comparison_days?: number;
  dimensions?: string[];
  max_results?: number;
}

export interface RootCauseInvestigationResponse {
  request: RootCauseInvestigationRequest;
  summary: AnomalySummary;
  decomposition: VolumeValueDecomposition | null;
  ranked_contributors: DimensionContributor[];
  operational_indicators: OperationalIndicators;
  explanation: string;
  limitations: string;
}

export interface AIInvestigationResponse {
  investigation_title: string;
  executive_summary: string;
  key_findings: string[];
  business_interpretation: string[];
  recommended_actions: string[];
  limitations: string[];
  model: string;
  generated_at: string;
  is_fallback: boolean;
}

// Phase 8: Autonomous Investigation Agent Contracts
export type StepStatus = 'completed' | 'skipped' | 'terminated' | 'in_progress';

export interface InvestigationStepTrace {
  step_number: number;
  step_type: string;
  step_title: string;
  status: StepStatus;
  finding_summary?: string | null;
  details: Record<string, unknown>;
  executed_at: string;
  reason_if_skipped?: string | null;
}

export interface RankedRootCause {
  rank: number;
  title: string;
  dimension: string;
  dimension_value: string;
  contribution_pct: number;
  absolute_change: number;
  score: number;
  explanation: string;
  causal_category?: 'macro_driver' | 'operational_mechanism' | 'segment_concentration';
  causal_mechanism?: string | null;
  affected_dimension?: string | null;
  affected_value?: string | null;
  evidence_chain?: string[];
  evidence_strength?: 'high' | 'medium' | 'low' | 'insufficient';
  confidence?: number;
}

export interface InvestigationAgentRequest {
  metric: MetricType;
  anomaly_date: string;
  comparison_days?: number;
  dimensions?: string[];
  max_investigation_steps?: number;
  minimum_contribution_pct?: number;
  minimum_severity?: AnomalySeverity;
}

export interface InvestigationAgentResponse {
  investigation_id: string;
  anomaly_summary: AnomalySummary;
  investigation_status: 'completed' | 'early_terminated' | 'max_steps_reached';
  steps_executed: number;
  trace: InvestigationStepTrace[];
  decomposition: VolumeValueDecomposition | null;
  top_root_causes: RankedRootCause[];
  supporting_evidence: DimensionContributor[];
  operational_signals: OperationalIndicators;
  executive_summary: string;
  key_findings: string[];
  recommended_actions: string[];
  limitations: string;
  termination_reason: string;
  model: string;
  is_fallback: boolean;
  generated_at: string;
  evidence_graph?: EvidenceGraph | null;
}

// Phase M: Structured Evidence Graph, Replay & Challenge Types
export type NodeType =
  | 'INCIDENT'
  | 'ANOMALY'
  | 'DRIVER'
  | 'EVIDENCE'
  | 'SEGMENT'
  | 'CORROBORATION'
  | 'ROOT_CAUSE';

export type EdgeRelation =
  | 'DETECTED_AS'
  | 'DECOMPOSED_INTO'
  | 'SUPPORTED_BY'
  | 'CONCENTRATED_IN'
  | 'CORROBORATED_BY'
  | 'ATTRIBUTED_TO';

export interface ConfidenceInterval {
  point_estimate: number;
  lower_bound?: number | null;
  upper_bound?: number | null;
  confidence_level: number;
  standard_error?: number | null;
  method: string;
  is_computable: boolean;
}

export interface GraphNode {
  node_id: string;
  node_type: NodeType;
  title: string;
  description: string;
  metric_name?: string | null;
  observed_value?: number | null;
  baseline_value?: number | null;
  contribution_pct?: number | null;
  absolute_change?: number | null;
  confidence: number;
  causal_level: 'descriptive' | 'associational' | 'mechanistic' | 'causal';
  causal_hierarchy_tier: number;
  confidence_interval?: ConfidenceInterval | null;
  provenance_query_id?: string | null;
  details?: Record<string, unknown>;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  relation: EdgeRelation;
  label: string;
  weight: number;
  is_primary_path: boolean;
  details?: Record<string, unknown>;
}

export interface EvidenceGraph {
  graph_id: string;
  created_at: string;
  root_node_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  primary_chain_node_ids: string[];
  summary_metrics: {
    total_nodes: number;
    total_edges: number;
    max_depth: number;
    overall_confidence: number;
    primary_driver?: string;
  };
}

export interface EvidenceEvaluation {
  evidence_title: string;
  observed_fact: string;
  verdict: 'supports_top_cause' | 'contradicts_candidate' | 'weak_link' | 'inconclusive';
  numerical_proof: string;
}

export interface ChallengeRequest {
  session_id: string;
  challenge_type: 'why_not_cause' | 'contradicting_evidence' | 'weakest_link' | 'what_would_change';
  candidate_cause?: string | null;
}

export interface ChallengeResponse {
  session_id: string;
  challenge_type: string;
  challenge_question: string;
  verdict_summary: string;
  top_ranked_cause: string;
  evaluations: EvidenceEvaluation[];
  confidence_impact: string;
  recommended_action: string;
  metadata?: Record<string, unknown>;
}

export interface ReplayStep {
  step_index: number;
  step_title: string;
  step_type: string;
  status: string;
  timestamp: string;
  active_node_id?: string | null;
  query_executed?: string | null;
  finding_summary?: string | null;
  intermediate_state?: Record<string, unknown>;
}

export interface InvestigationSnapshot {
  session_id: string;
  metric: string;
  anomaly_date: string;
  created_at: string;
  observed_value: number;
  baseline_value: number;
  total_steps: number;
  ranked_causes: RankedRootCause[];
  step_traces: InvestigationStepTrace[];
  evidence_graph?: EvidenceGraph | null;
  replay_steps: ReplayStep[];
  benchmark_version: string;
  metadata: Record<string, unknown>;
}

