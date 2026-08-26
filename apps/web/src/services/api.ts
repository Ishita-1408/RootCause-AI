/**
 * RootCause AI — Backend API Client
 */

import {
  AnomalyDetectionRequest,
  AnomalyDetectionResponse,
  RootCauseInvestigationRequest,
  RootCauseInvestigationResponse,
  AIInvestigationResponse,
  InvestigationAgentRequest,
  InvestigationAgentResponse,
  EvidenceGraph,
  ChallengeRequest,
  ChallengeResponse,
  InvestigationSnapshot,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export class APIError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorBody: unknown = null;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = await res.text();
      }

      const detail =
        typeof errorBody === 'object' && errorBody && 'detail' in errorBody
          ? String((errorBody as { detail: unknown }).detail)
          : `HTTP error ${res.status}`;

      throw new APIError(detail, res.status, errorBody);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof APIError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network communication failure';
    throw new APIError(message, 0);
  }
}

export const apiClient = {
  /** Check backend health */
  async checkHealth(): Promise<{ status: string }> {
    return request<{ status: string }>('/api/v1/health');
  },

  /** Check database readiness */
  async checkReadiness(): Promise<{ status: string; database: string }> {
    return request<{ status: string; database: string }>('/api/v1/ready');
  },

  /** Detect statistical time-series anomalies (Phase 5A) */
  async detectAnomalies(req: AnomalyDetectionRequest): Promise<AnomalyDetectionResponse> {
    return request<AnomalyDetectionResponse>('/api/v1/anomalies/detect', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Run deterministic root-cause drill-down (Phase 5B) */
  async investigateRootCause(req: RootCauseInvestigationRequest): Promise<RootCauseInvestigationResponse> {
    return request<RootCauseInvestigationResponse>('/api/v1/rootcause/investigate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Run end-to-end AI Executive Investigation (Phase 5C) */
  async investigateWithAI(req: RootCauseInvestigationRequest): Promise<AIInvestigationResponse> {
    return request<AIInvestigationResponse>('/api/v1/ai/investigate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Run Autonomous Investigation Agent (Phase 8) */
  async investigateWithAgent(req: InvestigationAgentRequest): Promise<InvestigationAgentResponse> {
    return request<InvestigationAgentResponse>('/api/v1/agent/investigate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Synthesize AI memo directly from pre-computed evidence */
  async explainWithAI(evidence: RootCauseInvestigationResponse): Promise<AIInvestigationResponse> {
    return request<AIInvestigationResponse>('/api/v1/ai/explain', {
      method: 'POST',
      body: JSON.stringify(evidence),
    });
  },

  /** Retrieve Evidence Graph for a session */
  async getEvidenceGraph(sessionId: string): Promise<EvidenceGraph> {
    return request<EvidenceGraph>(`/api/v1/agent/graph/${sessionId}`);
  },

  /** Execute counterfactual challenge mode evaluation */
  async evaluateChallenge(req: ChallengeRequest): Promise<ChallengeResponse> {
    return request<ChallengeResponse>('/api/v1/agent/challenge', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /** Retrieve investigation replay snapshot */
  async getReplaySnapshot(sessionId: string): Promise<InvestigationSnapshot> {
    return request<InvestigationSnapshot>(`/api/v1/agent/replay/${sessionId}`);
  },

  /** List available replay sessions */
  async getReplaySessions(): Promise<string[]> {
    return request<string[]>('/api/v1/agent/replay/sessions');
  },
};
