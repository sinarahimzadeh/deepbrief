# DeepBrief

DeepBrief is a multi-agent AI research platform. A supervisor delegates a question to parallel researcher agents, then writer and citation-verifier agents produce an evidence-grounded report.

The implementation scope and engineering plan are documented in [DEEPBRIEF_IMPLEMENTATION_SPEC.md](DEEPBRIEF_IMPLEMENTATION_SPEC.md).

## Planned stack

- Python 3.13 and FastAPI
- LangChain and LangGraph
- Google Gemini 3.5 Flash-Lite
- PostgreSQL and pgvector
- Next.js, React, and TypeScript

## Current milestone

The complete in-memory research and verification flow is working:

- `GET /api/v1/health` is available from FastAPI.
- `GET /api/v1/config/models` exposes the fixed Gemini model and quota status without secrets.
- `POST /api/v1/research` accepts and validates a research question.
- `GET /api/v1/research/{id}` returns live agent progress, findings, and sources.
- One LangChain factory creates Gemini 3.5 Flash-Lite chat models.
- A quota guard pauses model calls after Google reports the daily free limit.
- The Gemini supervisor produces exactly three validated, non-overlapping research assignments.
- LangGraph runs the three assigned Gemini researchers in parallel.
- Tavily keyless search supplies real web evidence without an account, API key, or paid fallback.
- Every researcher finding is validated against the returned source IDs.
- A dedicated writer turns the three research tracks into one structured report.
- Deterministic checks reject missing or invented source references before verification.
- A citation-verifier agent labels important claims as supported, weak, or unsupported.
- The Next.js research page shows live workflow states, the final report, verification results,
  and clickable inline citations.
- Jobs are temporarily stored in memory until PostgreSQL is added.
- PostgreSQL persistence, saved history, and pgvector retrieval are the next milestone.
- Backend tests and linting pass.
- The frontend production build passes.

## Run locally

Open two PowerShell terminals from the repository root.

Terminal 1:

```powershell
cd backend
uv sync
uv run fastapi dev app/main.py
```

Terminal 2:

```powershell
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`. FastAPI documentation is available at `http://localhost:8000/docs`.

The Gemini API key is optional during setup. To enable model calls, copy
`backend/.env.example` to `backend/.env` and add `GOOGLE_API_KEY`. The `.env`
file is ignored by Git. DeepBrief has no OpenAI integration or paid fallback.

Web search uses Tavily's free keyless mode. It requires no additional key and
stops with a normal error if Tavily's keyless rate limit is reached.

## Verify

```powershell
cd backend
uv run ruff check .
uv run pytest
```

```powershell
cd frontend
pnpm lint
pnpm build
```
