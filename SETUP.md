# ReleaseShield Setup Guide

This guide will walk you through setting up and running ReleaseShield on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.11+**
- **Node.js 18+**
- **uv** (Fast Python package installer and resolver)
- **pnpm** (Fast, disk space efficient package manager)

---

## 1. Environment Setup

ReleaseShield requires a few API keys and a database connection to function. 

1. Create a copy of the `.env.example` file and name it `.env` in the root of the project.
2. Fill in the following variables:

### Database (Supabase)
We use Supabase as our managed PostgreSQL database. 
1. Go to [Supabase](https://supabase.com) and create a new project.
2. Under **Project Settings -> Database**, switch the Connection Mode to **Session Pooler**.
3. Copy the URL and add your password (URL-encoded). It should look like this:
```env
DATABASE_URL=postgresql://postgres.yourproject:password%40123@aws-0-region.pooler.supabase.com:5432/postgres
```

### API Keys
1. **GitHub Token**: Generate a Classic Personal Access Token on [GitHub Developer Settings](https://github.com/settings/tokens) with the `repo` scope.
2. **LLM API Key**: Generate a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
3. Add both to your `.env` file:
```env
GITHUB_TOKEN=ghp_your_github_token_here
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-3.8-flash
```

---

## 2. Backend Setup

The backend is built with FastAPI, LangGraph, and SQLAlchemy.

1. Navigate to the `backend` folder:
```bash
cd backend
```
2. Create a virtual environment and install the dependencies using `uv`:
```bash
uv sync
```
3. Initialize the Supabase database (run migrations) and seed it with some historical baseline data:
```bash
uv run alembic upgrade head
uv run python -m scripts.collect_historical_releases --repository facebook/react --releases 10
```

---

## 3. Frontend Setup

The frontend is built with React, Vite, and Tailwind CSS v4.

1. Open a new terminal and navigate to the `frontend` folder:
```bash
cd frontend
```
2. Install the dependencies using `pnpm`:
```bash
pnpm install
```

---

## 4. Running the Application

To run the application, you will need two active terminal windows:

### Terminal 1: Backend Server
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend Server
```bash
cd frontend
pnpm run dev
```

### You're done! 🎉
Open your browser and navigate to `http://localhost:5173/`. 
Type in a repository name (e.g., `facebook/react`) and a release tag (e.g., `v19.0.0`) and click **Analyze Release** to see your Agentic Software Risk Advisor in action!
