# ReleaseShield Setup & Execution Guide

ReleaseShield is an agentic, explainable software release risk advisor. It evaluates release readiness across **Code**, **Test**, **Defect**, and **Operations** telemetry using a **Hybrid Risk Engine (XGBoost v3.4 + Deterministic Rule Gates)** and enforces a **Mandatory Human Gatekeeper Approval Workflow**.

---

## Prerequisites

Ensure the following tools are installed on your machine:
- **Python 3.11+**
- **Node.js 18+**
- **uv** (Fast Python package manager)
- **pnpm** (Fast Node.js package manager)

---

## 1. Environment Configuration

Check the `.env` file in the `ReleaseShield/` root directory:

```env
# Database (Auto-fallback to local SQLite if Supabase/PostgreSQL is unreachable)
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres

# GitHub Personal Access Token (for fetching public commit and PR metrics)
GITHUB_TOKEN=your_github_token_here

# Google Gemini API Key & Model (for executive report explanation)
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-3.8-flash
```

> **Note**: ReleaseShield includes automatic SQLite fallback (`releaseshield.db`). If your PostgreSQL or Supabase instance is offline or unreachable, the application starts and runs locally without crashing.

---

## 2. Running the Application

To run ReleaseShield, open **two terminal windows**:

### Terminal 1: Backend Server (FastAPI + LangGraph + XGBoost)

1. Open a terminal and navigate to the backend folder:
   ```bash
   cd ReleaseShield/backend
   ```

2. (First-time only) Install backend dependencies:
   ```bash
   uv sync
   uv pip install xgboost scikit-learn numpy --python .\.venv\Scripts\python.exe
   ```

3. Start the FastAPI development server:
   ```bash
   # On Windows PowerShell:
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # Or using uv directly:
   uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   - **Backend URL**: [http://localhost:8000](http://localhost:8000)
   - **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Terminal 2: Frontend Dashboard (React + TypeScript + Vite + Tailwind CSS)

1. Open a second terminal and navigate to the frontend folder:
   ```bash
   cd ReleaseShield/frontend
   ```

2. (First-time only) Install frontend dependencies:
   ```bash
   pnpm install
   ```

3. Start the Vite development server:
   ```bash
   pnpm run dev
   ```

   - **Frontend Dashboard URL**: [http://localhost:5173](http://localhost:5173)

---

## 3. How to Use ReleaseShield

1. Open your browser and navigate to **`http://localhost:5173/`**.
2. **Configure Release Context**:
   - **Repository**: Enter a repository (e.g. `facebook/react`).
   - **Target Release Tag**: Enter the release tag (e.g. `v19.0.0`).
   - **Release Type**: Select `MAJOR`, `MINOR`, `PATCH`, or `HOTFIX`.
   - **Target Environment**: Select `Production` or `Staging`.
3. **Select an Evaluation Scenario Preset**:
   - `Standard Healthy Release`: Low churn, 100% tests pass, 0 blockers.
   - `High Churn Hotfix`: High code churn, rushed PRs, elevated risk.
   - `Test Regression`: 8.6% drop in coverage, 85 failing tests, 12 flaky tests.
   - `Critical Blocker Defects`: 2 open P0 BLOCKER defects (RS-102, RS-109) triggering hard release gate.
   - `Operational Instability`: 2 staging rollbacks, 31.5% pipeline failure rate, infrastructure drift.
4. Click **Run Multi-Agent Risk Assessment**.
5. **Inspect the Assessment Results**:
   - **Overall Risk & Blended Score**: Weighted combination of deterministic rules and ML predictions.
   - **Hybrid Engine Breakdown**: Compare XGBoost ML probability vs. Deterministic Rule Score.
   - **Key Risk Drivers**: XGBoost feature importance attribution ranking the primary drivers of risk.
   - **The Four Domain Agents**: Inspect findings from Code Agent, Test Agent, Defect Agent, and Operations Agent.
   - **Required Actions Checklist**: Review concrete readiness tasks and check off completed items.
   - **Mandatory Human Gatekeeper Sign-Off**:
     - Automated deployment is disabled by design.
     - Reviewers (e.g. Release Manager, QA Lead) submit formal `Approve` or `Reject` decisions with audit notes.
