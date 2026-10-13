# DeepBrief API

FastAPI backend for DeepBrief.

## Development

```powershell
uv sync
uv run fastapi dev app/main.py
```

The API is available at `http://localhost:8000` and the interactive documentation is at `http://localhost:8000/docs`.

Current research endpoints:

- `POST /api/v1/research` creates a job and starts the Gemini supervisor.
- `GET /api/v1/research/{id}` returns status and exactly three planned assignments.

Jobs currently live in memory and are cleared when FastAPI restarts. PostgreSQL
persistence is a later milestone.

## Gemini model

Copy `.env.example` to `.env`, then add a free Google Gemini API key. DeepBrief
uses only `gemini-3.5-flash-lite`; it has no OpenAI or paid-model fallback.

`GET /api/v1/config/models` exposes the model name and availability, but never
the API key. All model calls must go through `invoke_chat_model`, which pauses
calls until the next midnight-Pacific reset after Google reports that the daily
free quota has been exhausted.

