# ReleaseShield: Multi-Agent Software Release Risk Advisor

ReleaseShield is an AI-powered, multi-agentic workflow that evaluates software release readiness across **Code**, **Test**, **Defect**, and **Operations** telemetry.

It combines deterministic safety rules with an **XGBoost v3.4 Machine Learning model** into a **Hybrid Risk Engine** that outputs explainable risk scores, key risk drivers, actionable required actions, and enforces **Mandatory Human Gatekeeper Sign-Off**.

---

## Core Capabilities & Architecture

| Capability | Implementation |
| :--- | :--- |
| **Multi-Domain Inputs** | Git/Code churn, CI Test suite results, Jira Defect telemetry, Operations/Deployment telemetry, and Release Context. |
| **The 4 Domain Agents** | **Code Agent**, **Test Agent**, **Defect Agent**, and **Operations Agent** coordinated via LangGraph. |
| **Hybrid Risk Engine** | Blends deterministic safety hard-gates with **XGBoost (v3.4)** ML probabilistic scoring and feature importance attribution. |
| **Key Risk Drivers** | Quantitative percentage contribution of each feature to the total release risk. |
| **Practical Recommendations** | Concrete release-readiness steps (e.g. "Resolve 2 Blocker bugs RS-102, RS-109", "Run 2 green staging pipelines"), not generic AI text. |
| **Required Actions Checklist** | Structured release-gate checklist with priority levels (BLOCKER, HIGH, MEDIUM) and toggleable completion statuses. |
| **Mandatory Human Approval** | Human gatekeeper sign-off required (Release Manager / QA Lead); automated deployment is strictly disabled. |
| **Synthetic / Mock Adapters** | API adapter architecture supporting realistic synthetic datasets and presets for offline/academic evaluation. |
| **Resilient Database** | Seamless automatic fallback from Supabase/PostgreSQL to local SQLite (`releaseshield.db`). |

---

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, LangGraph, XGBoost 3.4, Scikit-learn, SQLAlchemy, Google GenAI SDK.
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Dependency Management**: `uv` (Python), `pnpm` (Frontend).

---

## Quick Start Guide

### 1. Start the Backend Server
```bash
cd ReleaseShield/backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API running at: `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 2. Start the Frontend Dashboard
```bash
cd ReleaseShield/frontend
pnpm run dev
```
Dashboard running at: `http://localhost:5173`.

---

## Evaluation Scenarios
The dashboard includes one-click scenario presets for testing:
1. **Standard Healthy Release** (Low risk)
2. **High Churn Hotfix / Rush Release** (High risk, rushed PRs)
3. **Test & Coverage Regression** (High risk, failing tests & coverage drops)
4. **Critical Blocker Defects** (Critical risk, hard gate triggered by P0 defects)
5. **Operational & CI/CD Instability** (Critical risk, staging rollbacks & pipeline failures)
