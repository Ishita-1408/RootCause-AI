# RootCause AI — 3-Minute Interactive Demo Script

This script provides an exact, structured walkthrough for exploring the live RootCause AI platform.

---

## Prerequisites
Ensure the development servers are running:
```bash
# Terminal 1: Backend API (http://localhost:8000)
uv run uvicorn apps.api.main:app --reload --port 8000

# Terminal 2: React Dashboard (http://localhost:5173)
cd apps/web && npm run dev
```
Open **`http://localhost:5173`** (or `http://localhost:8000` for Docker/unified mode).

---

## ⏱️ Timeline & Step-by-Step Walkthrough

### 00:00 – 00:30 | Business Anomaly Identification
- **Screen:** Navigate to **What Changed** (or **Overview**).
- **Action:**
  - Select **Metric:** `Total GMV (Revenue)`.
  - In the date selector, pick `2017-11-20`.
- **What to Observe:**
  - The rolling zero-lookahead Z-score anomaly detector flags a critical negative spike ($|z| = 3.42 > 2.5$).
  - Observed GMV dropped from baseline **R$ 31,300** down to **R$ 22,410** (**-28.4%**).

---

### 00:30 – 01:00 | Trigger Autonomous Agent Investigation
- **Screen:** Click **Run Analysis** (or navigate to **Agent Trace**).
- **Action:** Observe the Autonomous Agent execute its 5-stage plan in real time.
- **What to Observe:**
  - Step 1: `ANOMALY_DETECTION` (verifies statistical deviation).
  - Step 2: `DECOMPOSITION` (isolates Volume vs. AOV effects).
  - Step 3: `STATISTICAL_TEST` (runs two-sample Welch $t$-test).
  - Step 4: `DIMENSIONAL_DRILLDOWN` (evaluates Customer State and Seller slices).
  - Step 5: `SYNTHESIS` (fires Claim Verification Firewall).

---

### 01:00 – 01:30 | Reviewing Root Cause & Multiplicative Proof
- **Screen:** Navigate to **Why It Changed** (or **Overview**).
- **What to Observe:**
  - **Volume vs. AOV Decomposition:** Order volume contraction explains **88.5%** of the decline (-32 orders), while AOV shift explains only **11.5%**.
  - **Rank #1 Driver:** Carrier Logistics Transit Delay & SLA degradation outranks demographic slice concentration.
  - **Statistical Significance:** Welch $t$-statistic = $-4.12$, $p = 0.0004$, 95% Confidence Interval $[-35.2\%, -21.2\%]$.

---

### 01:30 – 02:00 | Inspecting the Forensic Evidence Graph (DAG)
- **Screen:** Navigate to **Evidence Graph** in the sidebar.
- **Action:** Click on individual nodes in the 7-tier DAG:
  - `node_incident_1` $\to$ `node_anomaly_1` $\to$ `node_driver_1` $\to$ `node_evidence_1` $\to$ `node_segment_1` $\to$ `node_corrob_1` $\to$ `node_root_cause_1`.
- **What to Observe:**
  - The inspector drawer updates instantly without flickering or network re-fetching.
  - Every node displays exact provenance query IDs (`query_volume_aov_decomposition`, `query_welch_t_test`).

---

### 02:00 – 02:30 | Executive Challenge Mode (Adversarial Audit)
- **Screen:** Navigate to **Challenge Mode**.
- **Action:**
  - Select Inquiry: *"Why was this candidate cause rejected?"*
  - Pick Candidate Cause: `Average Order Value (Pricing)`.
  - Click **Evaluate Challenge**.
- **What to Observe:**
  - The engine mathematically rejects pricing as the root cause (explains only 11.5% of decline, $p = 0.34 > 0.05$).
  - Evaluates *"Show weakest evidence"* to inspect sample size confidence bounds.

---

### 02:30 – 03:00 | Deterministic Replay & Leadership Memo
- **Screen:** Navigate to **Investigation Replay** and click **Play**.
- **What to Observe:**
  - The engine steps through intermediate analytical states chronologically with zero non-deterministic re-execution.
  - Navigate to **Recommendations** to review the verified, non-hallucinated leadership action plan.
