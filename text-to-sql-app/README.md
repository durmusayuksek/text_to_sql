# Text to SQL App

A clean full-stack starter for a single Question & Answer text-to-SQL application.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet

## Project Structure

```text
text-to-sql-app/
|-- frontend/
|-- backend/
|-- data/
`-- tests/
```

The central data catalog lives in `backend/app/catalog.py`. API routes should stay thin, and every executable SQL query must go through `backend/app/duckdb_layer/sql_validator.py`.

The `/api/ask` flow is controlled and linear:

```text
User Question -> Analysis Planner -> Query Agent -> SQL Validator -> DuckDB Query Runner -> Response Agent -> Final Answer
```

Agents do not execute SQL. The backend validates and runs every generated query.

Catalog columns can be marked sensitive with `sensitive=True` and a `redaction_strategy` of `omit`, `mask`, or `hash`. Response Agent OpenAI payloads are minimized and apply these catalog redaction rules before sending row samples or numeric summaries.

## Environment

Copy `.env.example` to `.env` and adjust values locally.

```bash
cp .env.example .env
```

Agent modes:

- `AGENT_MODE=mock`: default mode. Uses deterministic mocked agents and does not call OpenAI.
- `AGENT_MODE=openai`: uses OpenAI for the planner, Query Agent, and Response Agent.
- `QUERY_AGENT_MODE` is still supported as a backward-compatible fallback when `AGENT_MODE` is not set.

Debug responses:

- `DEBUG_QUERY_RESULTS=false`: default. API responses include generated SQL, but hide raw rows.
- `DEBUG_QUERY_RESULTS=true`: include limited query rows in `/api/ask` responses for debugging.
- `RESPONSE_AGENT_MAX_SAMPLE_ROWS=5`: controls how many sample rows the Response Agent can receive in OpenAI mode.

Required OpenAI settings for `openai` mode:

```text
OPENAI_API_KEY=
AGENT_MODE=mock
OPENAI_MODEL=gpt-4.1-mini
RESPONSE_AGENT_MAX_SAMPLE_ROWS=5
```

Do not commit `.env`. It is ignored by git.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`.

Visit `http://localhost:8000/health` to verify the API is running.
