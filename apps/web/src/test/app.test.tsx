import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from '../App';

describe('App Multi-View Integration & Rendering Test', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders all 7 views seamlessly without any runtime crashes', async () => {
    const mockAnomalyData = {
      metric: 'total_gmv',
      product_category: null,
      start_date: '2017-11-01',
      end_date: '2017-12-05',
      window: 7,
      z_threshold: 2.0,
      minimum_history: 7,
      total_observations: 35,
      anomalies_count: 2,
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

    const mockRcData = {
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

    const mockAiData = {
      investigation_title: 'Executive Investigation Memo',
      executive_summary: 'Revenue expanded significantly above baseline.',
      key_findings: ['Orders increased surge.'],
      business_interpretation: ['Strong Black Friday volume.'],
      recommended_actions: ['Monitor fulfillment capacity.'],
      limitations: ['Correlation only.'],
      model: 'gemini-2.5',
      is_fallback: false,
      generated_at: '2026-08-25T20:00:00Z',
    };

    const mockAgentData = {
      investigation_id: 'inv_123',
      investigation_status: 'completed',
      model: 'gemini-2.5',
      trace: [
        {
          step_number: 1,
          step_title: 'Detect Anomalies',
          status: 'completed',
          finding_summary: 'Found spike.',
        },
      ],
      top_root_causes: [
        {
          rank: 1,
          dimension: 'product_category',
          dimension_value: 'cama_mesa_banho',
          title: 'Bed & Bath Surge',
          score: 95.0,
          contribution_pct: 35.0,
          explanation: 'Major order spike.',
        },
      ],
      executive_summary: 'Agent completed diagnosis successfully.',
      recommended_actions: ['Prepare inventory.'],
      operational_signals: {
        observed_late_delivery_rate: 12.0,
        observed_avg_delivery_days: 10.0,
        observed_cancellation_rate: 0.1,
        observed_avg_review_score: 4.2,
      },
      steps_executed: 5,
      termination_reason: 'completed',
    };

    global.fetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/anomalies/detect')) return { ok: true, json: async () => mockAnomalyData };
      if (url.includes('/rootcause/investigate')) return { ok: true, json: async () => mockRcData };
      if (url.includes('/ai/investigate')) return { ok: true, json: async () => mockAiData };
      if (url.includes('/agent/investigate')) return { ok: true, json: async () => mockAgentData };
      return { ok: true, json: async () => ({ status: 'ok' }) };
    });

    const { container } = render(<App />);
    expect(container).toBeDefined();

    // 1. Verify Overview
    await waitFor(() => {
      expect(screen.getAllByText(/ROOTCAUSE AI/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/INVESTIGATION RESULT/i).length).toBeGreaterThan(0);
    });

    // 2. Click 'What Changed'
    fireEvent.click(screen.getByRole('button', { name: /What Changed Unusual changes & timeline/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/What Changed\?/i).length).toBeGreaterThan(0);
    });

    // 3. Click 'Why It Changed'
    fireEvent.click(screen.getByRole('button', { name: /Why It Changed Primary drivers & levers/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Why It Changed/i).length).toBeGreaterThan(0);
    });

    // 4. Click 'Evidence'
    fireEvent.click(screen.getByRole('button', { name: /Evidence Segment drivers & data/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Evidence & Drivers/i).length).toBeGreaterThan(0);
    });

    // 5. Click 'Recommendations'
    fireEvent.click(screen.getByRole('button', { name: /Recommendations Actionable leadership steps/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Recommendations & Action Plan/i).length).toBeGreaterThan(0);
    });

    // 6. Click 'Agent Trace'
    fireEvent.click(screen.getByRole('button', { name: /Agent Trace Investigation trail/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Agent Investigation Trace/i).length).toBeGreaterThan(0);
    });

    // 7. Click 'Evidence Graph'
    fireEvent.click(screen.getByRole('button', { name: /Evidence Graph Forensic DAG provenance/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Forensic Evidence Graph/i).length).toBeGreaterThan(0);
    });

    // 8. Click 'Challenge Mode'
    fireEvent.click(screen.getByRole('button', { name: /Challenge Mode Adversarial hypothesis audit/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Executive Challenge Mode/i).length).toBeGreaterThan(0);
    });

    // 9. Click 'Investigation Replay'
    fireEvent.click(screen.getByRole('button', { name: /Investigation Replay Deterministic step playback/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Deterministic Investigation Replay/i).length).toBeGreaterThan(0);
    });

    // 10. Click 'Data Health'
    fireEvent.click(screen.getByRole('button', { name: /Data Health Integrity & data checks/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/Data Health & Integrity Status/i).length).toBeGreaterThan(0);
    });
  });
});
