# Camunda AI Operations Assistant

A production-style full-stack application that helps developers and workflow operators
investigate Camunda 8 process instances and incidents. It combines live Camunda
operational data, BPMN process definitions, RAG over operational documentation,
historical incident data, and an AI agent that decides which tools it needs — with
human approval required before any mutating Camunda operation.


## Architecture

```
frontend/                Angular
backend/
  app/
    api/                 FastAPI routes
    agents/              LangGraph investigation agent
    rag/                 Document ingestion + retrieval
    camunda/             CamundaClient abstraction and Camunda REST access
    database/            SQLAlchemy models / pgvector
    models/              Pydantic schemas shared across the API
    services/            Business logic (chat, etc.)
    config/              Environment-driven settings (pydantic-settings)
  tests/                 Pytest suite
docker-compose.yml        Postgres (pgvector) + backend + frontend for local dev
```

Design principles:
- The frontend never holds Camunda or LLM credentials — only the backend does.
- Camunda access goes through a `CamundaClient` abstraction so the rest of the app
  never depends on HTTP implementation details.
- The LLM/embedding provider is selected via environment variables so it can be
  swapped without touching application logic.
- Agent logic, RAG retrieval, and Camunda integration are kept as separate layers.

## Tech stack

- **Frontend:** Angular
- **Backend:** Python, FastAPI, Pydantic, LangChain, LangGraph
- **Database:** PostgreSQL + pgvector
- **Workflow platform:** Camunda 8 (local dev environment)
- **Infra:** Docker Compose

## Getting started (local development)

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker (optional, for the full Compose stack)

### 1. Start a local Camunda 8 cluster (C8Run)

This project talks to a real Camunda 8 cluster, so start one before running the
backend. The easiest option for local development is
[Camunda 8 Run](https://docs.camunda.io/docs/next/self-managed/setup/deploy/local/c8run/)
(`C8Run`), a self-contained distribution that bundles Zeebe, Operate, Tasklist, and
the REST API — no Docker required.

```powershell
.\c8run.exe start
.\c8run.exe stop
```

On Linux/macOS:

```bash
./start.sh
./shutdown.sh
```

Once it's up:
- REST API / Operate API base URL: `http://localhost:8080`
- Operate UI: `http://localhost:8080/operate`
- Tasklist UI: `http://localhost:8080/tasklist`

Stop the cluster with `.\shutdown.bat` (or `./shutdown.sh`) when you're done. State is
persisted between runs unless you delete C8Run's `data` directory.

### 2. Configure environment variables

Copy the credential template and add your API key values:

```bash
cp backend/.env.example backend/.env
```

`backend/.env` is ignored by Git and contains secrets only. Operational defaults,
including the Camunda endpoint, CORS origins, and model names, live in
`backend/app/config/settings.py`. `EMBEDDING_API_KEY` is optional; the LLM key is
used for embeddings when it is not set.

### 3. Run the backend

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000  
docker compose up -d postgres
```

Backend runs at http://localhost:8000. Interactive docs at http://localhost:8000/docs.
Chat messages longer than `CHAT_MESSAGE_WORD_LIMIT` words are reduced with an
extractive LexRank summary before they are sent to the investigation agent.

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000` and calls the backend via `http://localhost:8000`.

### 5. Run everything with Docker Compose

```bash
docker compose up --build
```

This starts Postgres (with pgvector), the FastAPI backend, and the Next.js frontend.

### 6. Run backend tests

```bash
cd backend
pytest -q
```

## API

All endpoints are prefixed with `/api` and return JSON. Operational data is fetched
from the cluster configured in `.env`; connection or upstream failures are returned as
HTTP 502 instead of substituting local data.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Service health, environment, Camunda mode |
| GET | `/api/process-instances` | List process instances |
| GET | `/api/process-instances/{key}` | Get a single process instance |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{key}` | Get a single incident |
| GET | `/api/process-definitions` | List process definitions |
| GET | `/api/process-definitions/{key}` | Get a single process definition |
| POST | `/api/chat` | Send a message to the investigation agent |

## Frontend dashboard

- **Overview** — active process instances, active incidents, recent failures
- **Process Instances** — list + detail view
- **Incidents** — list + detail view
- **Process Definitions** — list + detail view
- **AI Investigation** — chat interface talking to `/api/chat`
- **Documents / Knowledge Base** — document ingestion and retrieval interface

## Security notes

- No Camunda or LLM credentials are ever sent to or stored in the frontend.
- All secrets are read from environment variables and never hardcoded.
- Per-user identity and authorization checks will apply to knowledge and operational
  resources, and strict separation between auth and the AI agent (the agent never
  receives raw secrets or access tokens).
