# DeepBrief API

FastAPI backend for DeepBrief.

## Development

```powershell
uv sync
uv run fastapi dev app/main.py
```

The API is available at `http://localhost:8000` and the interactive documentation is at `http://localhost:8000/docs`.

Current research endpoints:

- `POST /api/v1/research` creates a job and starts the LangGraph workflow.
- `GET /api/v1/research/{id}` returns the supervisor plan, three researcher
  progress records, evidence-grounded findings, the final cited report, citation
  verification results, and clickable source URLs.

After the parallel researchers finish, a writer node produces one structured
report. A verifier node then checks important claims against the collected
source snippets. Application code also rejects missing and invented source IDs
before the semantic verification call.

Jobs currently live in memory and are cleared when FastAPI restarts. PostgreSQL
persistence is a later milestone.

## Gemini model

Copy `.env.example` to `.env`, then add a free Google Gemini API key. DeepBrief
uses only `gemini-3.5-flash-lite`; it has no OpenAI or paid-model fallback.

`GET /api/v1/config/models` exposes the model name and availability, but never
the API key. All model calls must go through `invoke_chat_model`, which pauses
calls until the next midnight-Pacific reset after Google reports that the daily
free quota has been exhausted.

## Web search

The three researcher nodes use Tavily's free keyless Search API. No Tavily key,
account, or payment method is required. Searches are bounded to four queries and
five accepted sources per researcher. When the keyless rate limit is reached,
the job stops without switching to a paid service.

