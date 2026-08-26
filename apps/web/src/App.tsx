import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavSection } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { CurrentInvestigationContext } from './components/CurrentInvestigationContext';
import { InvestigationStepper } from './components/InvestigationStepper';
import { OverviewView } from './components/views/OverviewView';
import { AnomaliesView } from './components/views/AnomaliesView';
import { RootCauseView } from './components/views/RootCauseView';
import { AIMemoView } from './components/views/AIMemoView';
import { AutonomousAgentView } from './components/views/AutonomousAgentView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { DataHealthView } from './components/views/DataHealthView';
import { EvidenceGraphView } from './components/views/EvidenceGraphView';
import { ChallengeModeView } from './components/views/ChallengeModeView';
import { ReplayView } from './components/views/ReplayView';
import { apiClient } from './services/api';
import {
  MetricType,
  AnomalyDetectionResponse,
  RootCauseInvestigationResponse,
  AIInvestigationResponse,
  InvestigationAgentResponse,
} from './types/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  // Navigation & Layout States
  const [activeSection, setActiveSection] = useState<NavSection>('overview');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  // Query Parameters States
  const [metric, setMetric] = useState<MetricType>('total_gmv');
  const [startDate, setStartDate] = useState<string>('2017-11-01');
  const [endDate, setEndDate] = useState<string>('2017-12-05');
  const [selectedDate, setSelectedDate] = useState<string>('2017-11-24');

  // Analytical Data States
  const [anomalyData, setAnomalyData] = useState<AnomalyDetectionResponse | null>(null);
  const [rootCauseData, setRootCauseData] = useState<RootCauseInvestigationResponse | null>(null);
  const [aiData, setAiData] = useState<AIInvestigationResponse | null>(null);
  const [agentData, setAgentData] = useState<InvestigationAgentResponse | null>(null);

  // Service Status & Diagnostics States
  const [apiStatus, setApiStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [lastAnalysisTime, setLastAnalysisTime] = useState<string | null>(null);
  const [isLoadingAnomalies, setIsLoadingAnomalies] = useState<boolean>(false);
  const [isLoadingDiagnostics, setIsLoadingDiagnostics] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Check API & Database Health
  const checkHealth = useCallback(async () => {
    try {
      setApiStatus('checking');
      await apiClient.checkHealth();
      setApiStatus('healthy');
    } catch {
      setApiStatus('unhealthy');
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Fetch Anomaly Time-Series
  const fetchAnomalies = useCallback(async () => {
    setIsLoadingAnomalies(true);
    setErrorMessage(null);
    try {
      const resp = await apiClient.detectAnomalies({
        metric,
        start_date: startDate,
        end_date: endDate,
        window: 7,
        z_threshold: 2.0,
      });
      setAnomalyData(resp);
      setLastAnalysisTime(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch anomaly detection time-series';
      setErrorMessage(msg);
    } finally {
      setIsLoadingAnomalies(false);
    }
  }, [metric, startDate, endDate]);

  // Fetch Root-Cause, AI Memo, and Autonomous Agent
  const fetchInvestigation = useCallback(
    async (dateToInvestigate: string) => {
      setIsLoadingDiagnostics(true);
      setErrorMessage(null);
      try {
        // 1. Fetch deterministic root-cause investigation
        const rcResp = await apiClient.investigateRootCause({
          metric,
          anomaly_date: dateToInvestigate,
          comparison_days: 7,
          dimensions: ['product_category', 'customer_state', 'seller'],
          max_results: 6,
        });
        setRootCauseData(rcResp);

        // 2. Fetch AI Executive Memo
        const aiResp = await apiClient.investigateWithAI({
          metric,
          anomaly_date: dateToInvestigate,
          comparison_days: 7,
          dimensions: ['product_category', 'customer_state', 'seller'],
        });
        setAiData(aiResp);

        // 3. Fetch Autonomous Investigation Agent
        const agentResp = await apiClient.investigateWithAgent({
          metric,
          anomaly_date: dateToInvestigate,
          comparison_days: 7,
          dimensions: ['product_category', 'customer_state', 'seller'],
          max_investigation_steps: 6,
          minimum_contribution_pct: 5.0,
        });
        setAgentData(agentResp);
        setLastAnalysisTime(new Date().toLocaleTimeString());
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to execute investigation pipeline';
        setErrorMessage(msg);
      } finally {
        setIsLoadingDiagnostics(false);
      }
    },
    [metric]
  );

  // Initial Data Fetch
  useEffect(() => {
    fetchAnomalies();
    fetchInvestigation(selectedDate);
  }, [fetchAnomalies, fetchInvestigation, selectedDate]);

  // Handler for selecting an anomaly date
  const handleSelectDate = (newDate: string) => {
    setSelectedDate(newDate);
    fetchInvestigation(newDate);
  };

  // Full Analysis Run Trigger
  const handleRunAnalysis = () => {
    checkHealth();
    fetchAnomalies();
    fetchInvestigation(selectedDate);
  };

  const isLoadingTotal = isLoadingAnomalies || isLoadingDiagnostics;

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* 1. Persistent Left Sidebar */}
      <Sidebar
        activeSection={activeSection}
        onSelectSection={setActiveSection}
        apiStatus={apiStatus}
        lastAnalysisTime={lastAnalysisTime}
        isOpenMobile={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* 2. Main Content Wrapper */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* Compact Top Bar */}
        <TopBar
          activeSection={activeSection}
          onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
          metric={metric}
          onChangeMetric={setMetric}
          startDate={startDate}
          onChangeStartDate={setStartDate}
          endDate={endDate}
          onChangeEndDate={setEndDate}
          onRunAnalysis={handleRunAnalysis}
          isLoading={isLoadingTotal}
        />

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {/* Global Event Switcher (shown when multiple anomalies exist) */}
          <CurrentInvestigationContext
            anomalyData={anomalyData}
            selectedDate={selectedDate}
            onSelectDate={handleSelectDate}
          />

          {/* Error Alert Banner */}
          {errorMessage && (
            <div className="glass-panel p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-start space-x-3 text-rose-300 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-bold">Investigation Request Notice: </span>
                {errorMessage}
              </div>
              <button
                onClick={handleRunAnalysis}
                className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 rounded text-white flex items-center space-x-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* Investigation Stepper Workflow (shown on investigation sections) */}
          {activeSection !== 'overview' && activeSection !== 'data-health' && (
            <InvestigationStepper
              activeSection={activeSection}
              onSelectSection={setActiveSection}
              selectedDate={selectedDate}
            />
          )}

          {/* 3. Section Views */}
          {activeSection === 'overview' && (
            <OverviewView
              anomalyData={anomalyData}
              rootCauseData={rootCauseData}
              aiData={aiData}
              metric={metric}
              selectedDate={selectedDate}
              onSelectDate={handleSelectDate}
              onNavigate={setActiveSection}
              isLoading={isLoadingTotal}
            />
          )}

          {activeSection === 'anomalies' && (
            <AnomaliesView
              data={anomalyData}
              selectedDate={selectedDate}
              onSelectDate={handleSelectDate}
              onNavigate={setActiveSection}
              metric={metric}
              isLoading={isLoadingAnomalies}
            />
          )}

          {activeSection === 'root-cause' && (
            <RootCauseView
              data={rootCauseData}
              isLoading={isLoadingDiagnostics}
              selectedDate={selectedDate}
            />
          )}

          {activeSection === 'evidence-graph' && (
            <EvidenceGraphView
              evidenceGraph={agentData?.evidence_graph}
              metric={metric}
              anomalyDate={selectedDate}
              onOpenChallenge={() => setActiveSection('challenge-mode')}
            />
          )}

          {activeSection === 'challenge-mode' && (
            <ChallengeModeView
              sessionId={agentData?.investigation_id || 'session_default_123'}
              metric={metric}
              anomalyDate={selectedDate}
            />
          )}

          {activeSection === 'replay' && (
            <ReplayView
              sessionId={agentData?.investigation_id || 'session_default_123'}
              metric={metric}
              anomalyDate={selectedDate}
            />
          )}

          {activeSection === 'ai-memo' && (
            <AIMemoView data={aiData} isLoading={isLoadingDiagnostics} />
          )}

          {activeSection === 'autonomous-agent' && (
            <AutonomousAgentView
              data={agentData}
              isLoading={isLoadingDiagnostics}
              selectedDate={selectedDate}
            />
          )}

          {activeSection === 'analytics' && (
            <AnalyticsView
              anomalyData={anomalyData}
              rootCauseData={rootCauseData}
              metric={metric}
              selectedDate={selectedDate}
              isLoading={isLoadingDiagnostics}
            />
          )}

          {activeSection === 'data-health' && (
            <DataHealthView apiStatus={apiStatus} onCheckHealth={checkHealth} />
          )}
        </main>

        {/* Modern Footer */}
        <footer className="border-t border-slate-900 bg-slate-950/80 py-4 px-6 text-center text-xs text-slate-500">
          RootCause AI © 2026 — Evidence-Backed Business Investigation Platform • Deterministic Analytical Marts
        </footer>
      </div>
    </div>
  );
};
