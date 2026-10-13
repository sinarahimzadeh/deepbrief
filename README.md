# DeepBrief

DeepBrief is a multi-agent AI research platform. A supervisor delegates a question to parallel researcher agents, then writer and citation-verifier agents produce an evidence-grounded report.

The implementation scope and engineering plan are documented in [DEEPBRIEF_IMPLEMENTATION_SPEC.md](DEEPBRIEF_IMPLEMENTATION_SPEC.md).

## Planned stack

- Python 3.13 and FastAPI
- LangChain and LangGraph
- OpenAI and Google Gemini
- PostgreSQL and pgvector
- Next.js, React, and TypeScript

## Current milestone

The first vertical slice is working:

- `GET /api/v1/health` is available from FastAPI.
- The Next.js home page checks the backend connection in the browser.
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
