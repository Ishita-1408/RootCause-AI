import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../services/api';

describe('RootCause AI API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('detectAnomalies calls /api/v1/anomalies/detect and returns data', async () => {
    const mockResponse = {
      metric: 'total_gmv',
      product_category: null,
      start_date: '2017-11-01',
      end_date: '2017-11-30',
      window: 7,
      z_threshold: 2.0,
      minimum_history: 7,
      total_observations: 30,
      anomalies_count: 1,
      results: [
        {
          date: '2017-11-24',
          metric: 'total_gmv',
          observed_value: 152653.74,
          baseline_mean: 31524.93,
          baseline_std: 9958.12,
          z_score: 12.16,
          severity: 'critical',
          is_anomaly: true,
          direction: 'increase',
        },
      ],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const res = await apiClient.detectAnomalies({
      metric: 'total_gmv',
      start_date: '2017-11-01',
      end_date: '2017-11-30',
    });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/anomalies/detect',
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(res.metric).toBe('total_gmv');
    expect(res.anomalies_count).toBe(1);
    expect(res.results[0].z_score).toBe(12.16);
  });

  it('investigateRootCause calls /api/v1/rootcause/investigate and returns data', async () => {
    const mockRc = {
      request: { metric: 'total_gmv', anomaly_date: '2017-11-24' },
      summary: {
        metric: 'total_gmv',
        anomaly_date: '2017-11-24',
        baseline_start_date: '2017-11-17',
        baseline_end_date: '2017-11-23',
        observed_value: 152653.74,
        baseline_value: 31524.93,
        absolute_change: 121128.81,
        percentage_change: 384.2,
        direction: 'increase',
      },
      decomposition: {
        observed_orders: 1176.0,
        baseline_orders: 207.0,
        observed_aov: 129.81,
        baseline_aov: 152.61,
        volume_effect: 147944.71,
        aov_effect: -4709.80,
        interaction_effect: -22103.00,
        total_change: 121128.81,
        volume_contribution_pct: 122.14,
        aov_contribution_pct: -3.89,
        interaction_contribution_pct: -18.25,
      },
      ranked_contributors: [
        {
          dimension: 'customer_state',
          dimension_value: 'SP',
          observed_value: 50000.0,
          baseline_value: 11448.32,
          absolute_change: 38551.68,
          percentage_change: 336.75,
          contribution_pct: 31.83,
          direction: 'increase',
          rank: 1,
        },
      ],
      operational_indicators: {
        observed_late_delivery_rate: 20.0,
        baseline_late_delivery_rate: 14.2,
        late_delivery_rate_change: 5.8,
        observed_avg_delivery_days: 17.2,
        baseline_avg_delivery_days: 12.5,
        avg_delivery_days_change: 4.7,
        observed_cancellation_rate: 0.4,
        baseline_cancellation_rate: 0.2,
        cancellation_rate_change: 0.2,
        observed_avg_review_score: 3.73,
        baseline_avg_review_score: 3.94,
        avg_review_score_change: -0.21,
      },
      explanation: 'TOTAL_GMV increased +384.2% on 2017-11-24.',
      limitations: 'Non-causal.',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRc,
    });

    const res = await apiClient.investigateRootCause({
      metric: 'total_gmv',
      anomaly_date: '2017-11-24',
    });

    expect(res.summary.percentage_change).toBe(384.2);
    expect(res.decomposition?.volume_effect).toBe(147944.71);
    expect(res.ranked_contributors[0].dimension_value).toBe('SP');
  });

  it('evaluateChallenge calls /api/v1/agent/challenge and returns evaluations', async () => {
    const mockChallenge = {
      session_id: 'test_sess_01',
      challenge_type: 'why_not_cause',
      challenge_question: 'Why was average_order_value rejected?',
      verdict_summary: 'AOV explains only 3.8% of variance.',
      top_ranked_cause: 'Volume Contraction',
      evaluations: [],
      confidence_impact: 'Confirmed',
      recommended_action: 'Focus on volume',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockChallenge,
    });

    const res = await apiClient.evaluateChallenge({
      session_id: 'test_sess_01',
      challenge_type: 'why_not_cause',
      candidate_cause: 'average_order_value',
    });

    expect(res.session_id).toBe('test_sess_01');
    expect(res.verdict_summary).toContain('3.8%');
  });

  it('handles API errors cleanly throwing APIError', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'Invalid metric unapproved_kpi' }),
    });

    await expect(
      apiClient.detectAnomalies({
        metric: 'total_gmv',
        start_date: '2018-01-01',
        end_date: '2018-01-10',
      })
    ).rejects.toThrow('Invalid metric unapproved_kpi');
  });
});
