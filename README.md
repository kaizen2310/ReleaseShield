# ReleaseShield: Agentic Software Release Risk Advisor

ReleaseShield is an AI-powered, agentic workflow that analyzes GitHub repository metrics to determine the risk of a software release. 

It uses deterministic historical baseline comparison (feature engineering) and LangGraph agent orchestration to evaluate risk. Finally, it uses Google Gemini purely to explain the structured evidence in an explainable, factual way.

## Tech Stack
- **Backend**: Python, FastAPI, LangGraph, Google GenAI SDK, PostgreSQL (SQLAlchemy).
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Infrastructure**: Docker, Docker Compose, `uv` (Fast Python package installer), `pnpm`.

---

## Prerequisites
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
- [uv](https://github.com/astral-sh/uv) (for blazing-fast Python dependency management)
- [pnpm](https://pnpm.io/installation) (for Frontend package management)
- Python 3.10+
- Node.js 18+

---

## 1. Environment Setup

At the root of the project, copy the `.env.example` file to create a `.env` file:

```bash
cp .env.example .env
```

Open the `.env` file and populate it with your API keys:
```env
# Database (Local Postgres)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=releaseshield
POSTGRES_PORT=5432

# (Alternative) Use Supabase instead of local Postgres
# DATABASE_URL=postgresql://postgres.xxx:password@aws-0-xx.pooler.supabase.com:6543/postgres

# GitHub Authentication
GITHUB_TOKEN=your_github_token_here


# LLM Authentication
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-pro
```

---

## 2. Database Initialization

We run the PostgreSQL database locally using Docker. 

1. Start the database:
   ```bash
   docker-compose up -d db
   ```
2. Initialize the database and run the migrations:
   ```bash
   cd backend
   uv run alembic upgrade head
   ```
3. Fetch your first batch of historical baselines (e.g., for `facebook/react`), by running the data collection script:

   ```bash
   uv run python -m scripts.collect_historical_releases --repository facebook/react --releases 10
   ```
   *(This step takes a few minutes as it fetches commits, pull requests, and file churn data from GitHub and caches it locally).*

---

## 3. Running the Backend (FastAPI)

To run the backend API server locally (for development):

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies via `uv`:
   ```bash
   uv sync
   ```
3. Run the FastAPI development server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
   The backend will be available at `http://localhost:8000`. You can view the swagger documentation at `http://localhost:8000/docs`.

---

## 4. Running the Frontend (React Dashboard)

Open a new terminal window to start the frontend:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies using `pnpm`:
   ```bash
   pnpm install
   ```
3. Start the Vite development server:
   ```bash
   pnpm run dev
   ```
   The frontend dashboard will be available at `http://localhost:5173`.

---

## 5. Usage

1. Open your browser and navigate to `http://localhost:5173`.
2. Enter the repository owner and name (e.g., `facebook/react`).
3. Enter the target release tag you wish to analyze (e.g., `v19.0.0`).
4. Click **Analyze Release**.
5. The LangGraph agent will:
   - Compare current metrics against the historical baseline in the PostgreSQL DB.
   - Run the rules engine to score anomalies (Code churn, large PRs, slow merges).
   - Feed the structured evidence to Gemini to generate an explainable Markdown report.
   - Display the results on the dashboard!

---

## (Optional) Running Tests

To verify the deterministic risk calculations and feature engineering:

```bash
cd backend
uv run pytest
```
