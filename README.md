# Camunda AI Operations Assistant

A production-style full-stack application that helps developers and workflow operators
investigate Camunda 8 process instances and incidents. It combines live Camunda
operational data, BPMN process definitions, RAG over operational documentation,
historical incident data, and an AI agent that decides which tools it needs — with
human approval required before any mutating Camunda operation.

This is **not** a "chat with PDF" app. RAG is one component of a larger operational
investigation workflow (see the phased roadmap below).

## Status

**Phase 1 (this repo, current state):** basic dashboard + read-only API backed by mock
data, so the full stack can be run and tested end to end before Camunda/RAG/agent
integrations are added.

## Architecture

```
frontend/                Next.js + TypeScript + Tailwind dashboard
backend/
  app/
    api/                 FastAPI routes
    agents/              LangGraph investigation agent (Phase 5+)
    rag/                 Document ingestion + retrieval (Phase 3+)
    camunda/             CamundaClient abstraction, mock/real modes (Phase 2+)
    database/            SQLAlchemy models / pgvector (Phase 3+)
    models/              Pydantic schemas shared across the API
    services/            Business logic (chat, mock data, etc.)
    config/              Environment-driven settings (pydantic-settings)
  tests/                 Pytest suite
docker-compose.yml        Postgres (pgvector) + backend + frontend for local dev
```

Design principles carried through every phase:
- The frontend never holds Camunda or LLM credentials — only the backend does.
- Camunda access goes through a `CamundaClient` abstraction so the rest of the app
  never depends on HTTP implementation details (Phase 2).
- The LLM/embedding provider is selected via environment variables so it can be
  swapped without touching application logic.
- Agent logic, RAG retrieval, and Camunda integration are kept as separate layers.

## Tech stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, Pydantic, LangChain, LangGraph
- **Database:** PostgreSQL + pgvector
- **Workflow platform:** Camunda 8 (local dev environment)
- **Infra:** Docker Compose

## Getting started (local development)

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker (optional, for the full Compose stack)

### 1. Configure environment variables

Fill in `LLM_API_KEY` / `EMBEDDING_API_KEY` etc. only when you reach the phases that
need them. Phase 1 runs entirely on mock data and does not require any API keys.

### 2. Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000 and calls the backend via `NEXT_PUBLIC_API_URL`
(defaults to `http://localhost:8000`).

### 4. Run everything with Docker Compose

```bash
docker compose up --build
```

This starts Postgres (with pgvector), the FastAPI backend, and the Next.js frontend.

### 5. Run backend tests

```bash
cd backend
pytest -q
```

## API (Phase 1)

All endpoints are prefixed with `/api` and return JSON. Data currently comes from an
in-memory mock service (`CAMUNDA_MODE=mock`); Phase 2 introduces a real Camunda-backed
mode (`CAMUNDA_MODE=real`) behind the same `CamundaClient` interface.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Service health, environment, Camunda mode |
| GET | `/api/process-instances` | List process instances |
| GET | `/api/process-instances/{key}` | Get a single process instance |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{key}` | Get a single incident |
| GET | `/api/process-definitions` | List process definitions |
| GET | `/api/process-definitions/{key}` | Get a single process definition |
| POST | `/api/chat` | Send a message to the investigation agent (placeholder reply in Phase 1) |

## Frontend dashboard (Phase 1)

- **Overview** — active process instances, active incidents, recent failures
- **Process Instances** — list + detail view
- **Incidents** — list + detail view
- **Process Definitions** — list + detail view
- **AI Investigation** — chat interface talking to `/api/chat`
- **Documents / Knowledge Base** — placeholder for the Phase 3 RAG ingestion UI

## Roadmap

1. ✅ Basic dashboard + read-only API over mock data
2. CamundaClient abstraction with mock/real modes, read-only Camunda operations
3. Document ingestion pipeline (Markdown/TXT/PDF) → pgvector, `search_knowledge`
4. Historical incident knowledge model, `search_similar_incidents`
5. LangGraph investigation agent with tool-calling
6. Structured investigation report (JSON) rendered as a report in the UI
7. Human-in-the-loop approval for mutating operations + audit log
8. Multi-user auth/authorization, secrets kept out of the agent
9. Hybrid retrieval (vector + BM25) with reranking
10. Evaluation harness (`python -m evaluation.run`) with Recall@K, MRR, faithfulness, etc.
11. Observability/logging of questions, retrievals, tool calls, latency, tokens
12. Full operations dashboard UI (BPMN visualization, evidence drill-down, approvals)

## Security notes

- No Camunda or LLM credentials are ever sent to or stored in the frontend.
- All secrets are read from environment variables and never hardcoded.
- Later phases add per-user identity, authorization checks on knowledge/operational
  resources, and strict separation between auth and the AI agent (the agent never
  receives raw secrets or access tokens).
