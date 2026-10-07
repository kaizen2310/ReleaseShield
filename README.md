# ReleaseShield - Agentic Software Release Risk Advisor

ReleaseShield is a Git-based release risk assessment system that uses GitHub API data, feature engineering, and a LangGraph-based Git Agent to evaluate and explain software release risk.

This MVP version calculates risk using deterministic metrics and repository-specific historical baselines. It does **not** use supervised machine learning. 

## Architecture

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy
- **AI Agent:** LangGraph, LLM for explanation
- **Infrastructure:** Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill in the `.env` file with your GitHub token and LLM API credentials.

### Running with Docker

Start the database and backend:

```bash
docker-compose up -d --build
```

The FastAPI backend will be available at: http://localhost:8000
The Health Check API is at: http://localhost:8000/api/health
Interactive API docs are at: http://localhost:8000/docs
